USE food_delivery;

-- ------------------------------------------------------------
-- States & major cities (subset of all Indian states/UTs)
-- ------------------------------------------------------------
INSERT INTO states (name) VALUES
('Andhra Pradesh'),('Arunachal Pradesh'),('Assam'),('Bihar'),('Chhattisgarh'),
('Goa'),('Gujarat'),('Haryana'),('Himachal Pradesh'),('Jharkhand'),
('Karnataka'),('Kerala'),('Madhya Pradesh'),('Maharashtra'),('Manipur'),
('Meghalaya'),('Mizoram'),('Nagaland'),('Odisha'),('Punjab'),
('Rajasthan'),('Sikkim'),('Tamil Nadu'),('Telangana'),('Tripura'),
('Uttar Pradesh'),('Uttarakhand'),('West Bengal'),
('Andaman and Nicobar Islands'),('Chandigarh'),
('Dadra and Nagar Haveli and Daman and Diu'),('Delhi'),
('Jammu and Kashmir'),('Ladakh'),('Lakshadweep'),('Puducherry');

INSERT INTO cities (state_id, name)
SELECT id, 'Ahmedabad' FROM states WHERE name='Gujarat'
UNION ALL SELECT id,'Surat' FROM states WHERE name='Gujarat'
UNION ALL SELECT id,'Vadodara' FROM states WHERE name='Gujarat'
UNION ALL SELECT id,'Rajkot' FROM states WHERE name='Gujarat'
UNION ALL SELECT id,'Mumbai' FROM states WHERE name='Maharashtra'
UNION ALL SELECT id,'Pune' FROM states WHERE name='Maharashtra'
UNION ALL SELECT id,'Nagpur' FROM states WHERE name='Maharashtra'
UNION ALL SELECT id,'Nashik' FROM states WHERE name='Maharashtra'
UNION ALL SELECT id,'Bengaluru' FROM states WHERE name='Karnataka'
UNION ALL SELECT id,'Mysuru' FROM states WHERE name='Karnataka'
UNION ALL SELECT id,'Mangaluru' FROM states WHERE name='Karnataka'
UNION ALL SELECT id,'Chennai' FROM states WHERE name='Tamil Nadu'
UNION ALL SELECT id,'Coimbatore' FROM states WHERE name='Tamil Nadu'
UNION ALL SELECT id,'Madurai' FROM states WHERE name='Tamil Nadu'
UNION ALL SELECT id,'Hyderabad' FROM states WHERE name='Telangana'
UNION ALL SELECT id,'Warangal' FROM states WHERE name='Telangana'
UNION ALL SELECT id,'Kolkata' FROM states WHERE name='West Bengal'
UNION ALL SELECT id,'Howrah' FROM states WHERE name='West Bengal'
UNION ALL SELECT id,'Lucknow' FROM states WHERE name='Uttar Pradesh'
UNION ALL SELECT id,'Kanpur' FROM states WHERE name='Uttar Pradesh'
UNION ALL SELECT id,'Noida' FROM states WHERE name='Uttar Pradesh'
UNION ALL SELECT id,'Agra' FROM states WHERE name='Uttar Pradesh'
UNION ALL SELECT id,'Varanasi' FROM states WHERE name='Uttar Pradesh'
UNION ALL SELECT id,'Jaipur' FROM states WHERE name='Rajasthan'
UNION ALL SELECT id,'Jodhpur' FROM states WHERE name='Rajasthan'
UNION ALL SELECT id,'Udaipur' FROM states WHERE name='Rajasthan'
UNION ALL SELECT id,'New Delhi' FROM states WHERE name='Delhi'
UNION ALL SELECT id,'Dwarka' FROM states WHERE name='Delhi'
UNION ALL SELECT id,'Chandigarh' FROM states WHERE name='Chandigarh'
UNION ALL SELECT id,'Bhopal' FROM states WHERE name='Madhya Pradesh'
UNION ALL SELECT id,'Indore' FROM states WHERE name='Madhya Pradesh'
UNION ALL SELECT id,'Gwalior' FROM states WHERE name='Madhya Pradesh'
UNION ALL SELECT id,'Patna' FROM states WHERE name='Bihar'
UNION ALL SELECT id,'Gaya' FROM states WHERE name='Bihar'
UNION ALL SELECT id,'Kochi' FROM states WHERE name='Kerala'
UNION ALL SELECT id,'Thiruvananthapuram' FROM states WHERE name='Kerala'
UNION ALL SELECT id,'Kozhikode' FROM states WHERE name='Kerala'
UNION ALL SELECT id,'Chandigarh City' FROM states WHERE name='Punjab'
UNION ALL SELECT id,'Amritsar' FROM states WHERE name='Punjab'
UNION ALL SELECT id,'Ludhiana' FROM states WHERE name='Punjab'
UNION ALL SELECT id,'Gurugram' FROM states WHERE name='Haryana'
UNION ALL SELECT id,'Faridabad' FROM states WHERE name='Haryana'
UNION ALL SELECT id,'Bhubaneswar' FROM states WHERE name='Odisha'
UNION ALL SELECT id,'Cuttack' FROM states WHERE name='Odisha'
UNION ALL SELECT id,'Guwahati' FROM states WHERE name='Assam'
UNION ALL SELECT id,'Dibrugarh' FROM states WHERE name='Assam'
UNION ALL SELECT id,'Ranchi' FROM states WHERE name='Jharkhand'
UNION ALL SELECT id,'Jamshedpur' FROM states WHERE name='Jharkhand'
UNION ALL SELECT id,'Raipur' FROM states WHERE name='Chhattisgarh'
UNION ALL SELECT id,'Bilaspur' FROM states WHERE name='Chhattisgarh'
UNION ALL SELECT id,'Panaji' FROM states WHERE name='Goa'
UNION ALL SELECT id,'Margao' FROM states WHERE name='Goa'
UNION ALL SELECT id,'Dehradun' FROM states WHERE name='Uttarakhand'
UNION ALL SELECT id,'Haridwar' FROM states WHERE name='Uttarakhand'
UNION ALL SELECT id,'Shimla' FROM states WHERE name='Himachal Pradesh'
UNION ALL SELECT id,'Manali' FROM states WHERE name='Himachal Pradesh'
UNION ALL SELECT id,'Srinagar' FROM states WHERE name='Jammu and Kashmir'
UNION ALL SELECT id,'Jammu' FROM states WHERE name='Jammu and Kashmir'
UNION ALL SELECT id,'Leh' FROM states WHERE name='Ladakh'
UNION ALL SELECT id,'Agartala' FROM states WHERE name='Tripura'
UNION ALL SELECT id,'Imphal' FROM states WHERE name='Manipur'
UNION ALL SELECT id,'Shillong' FROM states WHERE name='Meghalaya'
UNION ALL SELECT id,'Aizawl' FROM states WHERE name='Mizoram'
UNION ALL SELECT id,'Kohima' FROM states WHERE name='Nagaland'
UNION ALL SELECT id,'Itanagar' FROM states WHERE name='Arunachal Pradesh'
UNION ALL SELECT id,'Gangtok' FROM states WHERE name='Sikkim'
UNION ALL SELECT id,'Puducherry Town' FROM states WHERE name='Puducherry'
UNION ALL SELECT id,'Port Blair' FROM states WHERE name='Andaman and Nicobar Islands'
UNION ALL SELECT id,'Daman' FROM states WHERE name='Dadra and Nagar Haveli and Daman and Diu'
UNION ALL SELECT id,'Kavaratti' FROM states WHERE name='Lakshadweep';

-- ------------------------------------------------------------
-- Categories
-- ------------------------------------------------------------
INSERT INTO categories (name, is_active) VALUES
('Pizza',1),('Burger',1),('Cold Drinks',1),('Dessert',1),('Biryani',1),
('Chinese',1),('South Indian',1),('Sandwich',1),('Pasta',1),('Snacks',1),
('Thali',1),('Cakes',1);

-- ------------------------------------------------------------
-- Admin (password: Admin@123 -- hash generated by backend seed script)
-- Restaurants and foods are seeded programmatically by
-- backend/utils/seed_runner.py so that password hashing and
-- price/discount math stay consistent with the app's own logic.
-- ------------------------------------------------------------

-- ------------------------------------------------------------
-- GK Question Bank (30 sample questions; add more via Admin panel)
-- ------------------------------------------------------------
INSERT INTO game_questions (question, option_a, option_b, option_c, option_d, correct_option, is_active) VALUES
('What is the capital of India?','Mumbai','New Delhi','Kolkata','Chennai','B',1),
('Which planet is known as the Red Planet?','Venus','Mars','Jupiter','Saturn','B',1),
('Who wrote the Indian national anthem?','Rabindranath Tagore','Bankim Chandra','Sarojini Naidu','Mahatma Gandhi','A',1),
('What is the largest ocean on Earth?','Atlantic','Indian','Arctic','Pacific','D',1),
('How many continents are there?','5','6','7','8','C',1),
('What is the currency of Japan?','Won','Yuan','Yen','Ringgit','C',1),
('Which gas do plants absorb from the atmosphere?','Oxygen','Nitrogen','Carbon Dioxide','Hydrogen','C',1),
('Who painted the Mona Lisa?','Van Gogh','Picasso','Leonardo da Vinci','Michelangelo','C',1),
('What is the tallest mountain in the world?','K2','Kangchenjunga','Everest','Makalu','C',1),
('Which is the longest river in India?','Yamuna','Godavari','Ganga','Brahmaputra','C',1),
('What is the chemical symbol for gold?','Gd','Au','Ag','Go','B',1),
('Which country hosted the 2016 Summer Olympics?','China','UK','Brazil','Russia','C',1),
('How many players are there in a cricket team?','9','10','11','12','C',1),
('What is the national animal of India?','Lion','Tiger','Elephant','Peacock','B',1),
('Which is the smallest planet in our solar system?','Earth','Mars','Mercury','Venus','C',1),
('Who is known as the Father of the Nation in India?','Jawaharlal Nehru','Mahatma Gandhi','Sardar Patel','Subhas Chandra Bose','B',1),
('What is H2O commonly known as?','Salt','Sugar','Water','Oxygen','C',1),
('Which festival is known as the Festival of Lights?','Holi','Diwali','Eid','Christmas','B',1),
('What is the fastest land animal?','Lion','Cheetah','Horse','Leopard','B',1),
('Which country gifted the Statue of Liberty to the USA?','UK','Germany','France','Italy','C',1),
('How many colors are there in a rainbow?','5','6','7','8','C',1),
('What is the boiling point of water at sea level (Celsius)?','90','95','100','110','C',1),
('Which Indian state is known as the Land of Five Rivers?','Punjab','Haryana','Rajasthan','Gujarat','A',1),
('Who invented the telephone?','Thomas Edison','Alexander Graham Bell','Nikola Tesla','James Watt','B',1),
('What is the national sport of India?','Cricket','Hockey','Football','Kabaddi','B',1),
('Which is the largest desert in the world?','Sahara','Gobi','Thar','Antarctic','D',1),
('Which planet has the most moons?','Earth','Saturn','Mars','Mercury','B',1),
('What is the square root of 64?','6','7','8','9','C',1),
('Which Indian city is known as the Silicon Valley of India?','Hyderabad','Pune','Bengaluru','Chennai','C',1),
('Who was the first Prime Minister of India?','Lal Bahadur Shastri','Jawaharlal Nehru','Indira Gandhi','Rajendra Prasad','B',1);
