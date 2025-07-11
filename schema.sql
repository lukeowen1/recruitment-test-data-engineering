-- create places table
CREATE TABLE IF NOT EXISTS places (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city VARCHAR(255) NOT NULL,
    county VARCHAR(255),
    country VARCHAR(255) NOT NULL,
    UNIQUE KEY unique_place (city, county, country)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- create people table
CREATE TABLE IF NOT EXISTS people (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    date_of_birth DATE NOT NULL,
    place_of_birth_id INT,
    FOREIGN KEY (place_of_birth_id) REFERENCES places(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- index for better query performance
CREATE INDEX idx_people_place_of_birth ON people(place_of_birth_id);
CREATE INDEX idx_places_country ON places(country);