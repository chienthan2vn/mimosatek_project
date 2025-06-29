-- Bảng 1: WateringSchedule 
CREATE TABLE WateringSchedule (
    id SERIAL PRIMARY KEY,
    time_waiting VARCHAR(255),
    time_watering TIMESTAMP,
    watering_traffic VARCHAR(255),
    environ_sensor_data JSONB,  
    reason TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng 2: Reflection
CREATE TABLE Reflection (
    id SERIAL PRIMARY KEY,
    reflextion_text TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng 3: OutputData
CREATE TABLE OutputData (
    id SERIAL PRIMARY KEY,
    ec_out FLOAT,
    time_full INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
