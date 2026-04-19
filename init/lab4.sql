-- COM2058 LAB4
-- Ankara University - Computer Engineering Department

-- =============================================
-- PART 1: TABLEL4 (GROUP BY / HAVING examples)
-- =============================================

DROP TABLE IF EXISTS TABLEL4;

CREATE TABLE TABLEL4 (
    A INT,
    B INT
);

INSERT INTO TABLEL4 (A, B) VALUES
(3, 10),
(3, 20),
(4, 30),
(4, 40),
(4, 50),
(5, 20);

-- Verification queries:
-- select A, sum(B), avg(B) from TABLEL4 group by A;
-- Expected: (3, 30, 15), (4, 120, 40), (5, 20, 20)

-- select A, sum(B), avg(B) from TABLEL4 group by A having sum(B) < 50;
-- Expected: (3, 30, 15), (5, 20, 20)


-- =============================================
-- PART 2: EMPLOYEES table
-- =============================================

DROP TABLE IF EXISTS EMPLOYEES;

CREATE TABLE EMPLOYEES (
    NAME VARCHAR(50),
    TEAM VARCHAR(20),
    SALARY DECIMAL(10,2),
    SICK_LEAVE INT,
    ANNUAL_LEAVE INT
);

INSERT INTO EMPLOYEES (NAME, TEAM, SALARY, SICK_LEAVE, ANNUAL_LEAVE) VALUES
('Ali',    'TeamA', 35000, 20, 25),
('Ayse',   'TeamA', 42000, 30, 20),
('Mehmet', 'TeamA', 38000, 15, 28),
('Zeynep', 'TeamB', 45000, 28, 22),
('Can',    'TeamB', 40000, 35, 30),
('Elif',   'TeamB', 38000, 22, 26),
('Burak',  'TeamC', 36000, 18, 24),
('Deniz',  'TeamC', 37000, 32, 20);


-- =============================================
-- ANSWERS
-- =============================================

-- Q1: Show the average salary in each team.
SELECT TEAM, AVG(SALARY) AS AVG_SALARY
FROM EMPLOYEES
GROUP BY TEAM;
-- TeamA: 38333.33
-- TeamB: 41000.00
-- TeamC: 36500.00

-- Q2: Find the teams that have average salaries under 39000.
SELECT TEAM, AVG(SALARY) AS AVG_SALARY
FROM EMPLOYEES
GROUP BY TEAM
HAVING AVG(SALARY) < 39000;
-- TeamA: 38333.33
-- TeamC: 36500.00

-- Q3: Find the salary of everyone with less than 25 days of sick leave, ordered by name.
SELECT NAME, SALARY
FROM EMPLOYEES
WHERE SICK_LEAVE < 25
ORDER BY NAME;
-- Ali:    35000
-- Burak:  36000
-- Elif:   38000
-- Mehmet: 38000

-- Q4: Find how many people on each team have less than 30 days of sick leave.
SELECT TEAM, COUNT(*) AS PERSON_COUNT
FROM EMPLOYEES
WHERE SICK_LEAVE < 30
GROUP BY TEAM;
-- TeamA: 2 (Ali, Mehmet)
-- TeamB: 2 (Zeynep, Elif)
-- TeamC: 1 (Burak)

-- Q5: Find people whose sick leave is more than annual leave.
SELECT NAME
FROM EMPLOYEES
WHERE SICK_LEAVE > ANNUAL_LEAVE;
-- Ayse  (30 > 20)
-- Can   (35 > 30)
-- Deniz (32 > 20)
