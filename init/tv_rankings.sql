CREATE TABLE tv_rankings (
    rank_no INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    channel string(50) NOT NULL,
    rating DECIMAL(3, 1) NOT NULL
);
INSERT INTO tv_rankings (name, type, channel, rating) VALUES
('COLD CASE', 'Serial', 'CNBC-E', 8.9),
('SEKSENLER', 'Serial', 'TRT 1', 7.5),
('STADYUM', 'Sport', 'TRT 1', 6.6),
('ATV ANA HABER', 'Newscast', 'ATV', 6.5),
('KANAL D HABER', 'Newscast', 'KANAL D', 5.2);
SELECT * FROM tv_rankings;
