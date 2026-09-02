import random
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g
from backend.models.models import (
    db, Customer, GameQuestion, GameSession, GameSessionQuestion, GameAnswer, GameReward,
)
from backend.middleware.auth_middleware import token_required
from backend.services.wallet_service import credit_wallet

game_bp = Blueprint("game", __name__, url_prefix="/api/game")

QUESTIONS_PER_GAME = 7
SECONDS_PER_QUESTION = 10
MIN_CORRECT_FOR_REWARD = 5
REWARD_MIN = 1
REWARD_MAX = 200


def _question_public(q: GameQuestion):
    return {
        "question_id": q.id,
        "question": q.question,
        "options": {"A": q.option_a, "B": q.option_b, "C": q.option_c, "D": q.option_d},
        "time_limit_seconds": SECONDS_PER_QUESTION,
        # correct_option intentionally omitted from the client payload
    }


@game_bp.route("/start", methods=["POST"])
@token_required(["customer"])
def start_game():
    customer = Customer.query.filter_by(user_id=g.user_id).first()

    pool = GameQuestion.query.filter_by(is_active=True).all()
    if len(pool) < QUESTIONS_PER_GAME:
        return jsonify({"error": "Not enough active questions in the question bank."}), 500

    # avoid repeats from the customer's most recent session where possible
    recent_session = (
        GameSession.query.filter_by(customer_id=customer.id, status="completed")
        .order_by(GameSession.id.desc()).first()
    )
    recent_ids = set()
    if recent_session:
        recent_ids = {sq.question_id for sq in GameSessionQuestion.query.filter_by(session_id=recent_session.id)}

    fresh_pool = [q for q in pool if q.id not in recent_ids]
    chosen_pool = fresh_pool if len(fresh_pool) >= QUESTIONS_PER_GAME else pool
    chosen = random.sample(chosen_pool, QUESTIONS_PER_GAME)

    session = GameSession(customer_id=customer.id, status="in_progress", started_at=datetime.utcnow())
    db.session.add(session)
    db.session.flush()

    for i, q in enumerate(chosen):
        db.session.add(GameSessionQuestion(session_id=session.id, question_id=q.id, position=i))
    db.session.commit()

    return jsonify({
        "session_id": session.id,
        "questions": [_question_public(q) for q in chosen],
        "total_questions": QUESTIONS_PER_GAME,
        "points_per_correct": 10,
        "max_score": QUESTIONS_PER_GAME * 10,
    }), 201


@game_bp.route("/answer", methods=["POST"])
@token_required(["customer"])
def submit_answer():
    """
    selected_option is 'A'|'B'|'C'|'D'|'TIMEOUT'. answer_time_seconds is how
    long the client says the user took; if it's over the 10s limit (with a
    small network grace period) the answer is scored as incorrect/timeout
    regardless of what option was selected, so the timer can't be bypassed
    client-side.
    """
    data = request.get_json(force=True) or {}
    session_id = data.get("session_id")
    question_id = data.get("question_id")
    selected_option = data.get("selected_option", "TIMEOUT")
    answer_time_seconds = float(data.get("answer_time_seconds", 999))

    customer = Customer.query.filter_by(user_id=g.user_id).first()
    session = GameSession.query.get(session_id)
    if not session or session.customer_id != customer.id:
        return jsonify({"error": "Game session not found."}), 404
    if session.status != "in_progress":
        return jsonify({"error": "This game session has already ended."}), 400

    link = GameSessionQuestion.query.filter_by(session_id=session.id, question_id=question_id).first()
    if not link:
        return jsonify({"error": "This question is not part of this session."}), 400
    if GameAnswer.query.filter_by(session_id=session.id, question_id=question_id).first():
        return jsonify({"error": "This question was already answered."}), 400

    question = GameQuestion.query.get(question_id)
    timed_out = answer_time_seconds > (SECONDS_PER_QUESTION + 2)  # small grace for network latency
    is_correct = (not timed_out) and selected_option == question.correct_option

    db.session.add(GameAnswer(
        session_id=session.id, question_id=question_id,
        selected_option="TIMEOUT" if timed_out else selected_option,
        is_correct=is_correct,
    ))
    db.session.commit()

    return jsonify({
        "correct": is_correct,
        "correct_option": question.correct_option,
    }), 200


@game_bp.route("/finish", methods=["POST"])
@token_required(["customer"])
def finish_game():
    data = request.get_json(force=True) or {}
    session_id = data.get("session_id")

    customer = Customer.query.filter_by(user_id=g.user_id).first()
    session = GameSession.query.get(session_id)
    if not session or session.customer_id != customer.id:
        return jsonify({"error": "Game session not found."}), 404
    if session.status == "completed":
        return jsonify({"error": "This game session was already finished."}), 400

    answers = GameAnswer.query.filter_by(session_id=session.id).all()
    correct_count = sum(1 for a in answers if a.is_correct)
    incorrect_count = len(answers) - correct_count
    score = correct_count * 10

    session.correct_count = correct_count
    session.score = score
    session.status = "completed"
    session.completed_at = datetime.utcnow()

    from backend.services import streak_service
    streak_service.record_activity(customer.id, source="game")

    reward_amount = 0.0
    # Server-side, tamper-proof reward generation. Guarded by the unique
    # constraint on game_rewards.session_id so a session can never pay out twice.
    if correct_count >= MIN_CORRECT_FOR_REWARD and not GameReward.query.filter_by(session_id=session.id).first():
        reward_amount = round(random.uniform(REWARD_MIN, REWARD_MAX), 2)
        session.reward_amount = reward_amount
        session.reward_claimed = True
        db.session.add(session)
        db.session.flush()

        wallet, txn = credit_wallet(
            customer.id, reward_amount,
            reason="General Knowledge Game reward",
            reference_type="game_reward", reference_id=session.id, txn_type="bonus",
        )
        reward = GameReward(session_id=session.id, customer_id=customer.id,
                             amount=reward_amount, wallet_transaction_id=txn.id)
        db.session.add(reward)

    db.session.commit()

    return jsonify({
        "session_id": session.id,
        "total_questions": len(answers) or QUESTIONS_PER_GAME,
        "correct_answers": correct_count,
        "incorrect_answers": incorrect_count,
        "score": score,
        "max_score": QUESTIONS_PER_GAME * 10,
        "reward_amount": reward_amount,
        "reward_earned": reward_amount > 0,
    }), 200


@game_bp.route("/history", methods=["GET"])
@token_required(["customer"])
def game_history():
    customer = Customer.query.filter_by(user_id=g.user_id).first()
    sessions = (
        GameSession.query.filter_by(customer_id=customer.id, status="completed")
        .order_by(GameSession.completed_at.desc()).all()
    )
    return jsonify([{
        "session_id": s.id, "correct_count": s.correct_count, "score": s.score,
        "reward_amount": float(s.reward_amount or 0), "completed_at": s.completed_at.isoformat() if s.completed_at else None,
    } for s in sessions]), 200
