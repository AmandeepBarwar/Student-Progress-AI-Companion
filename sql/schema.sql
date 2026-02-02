-- =========================================
-- Student Progress AI Companion
-- Database Schema
-- =========================================

CREATE DATABASE IF NOT EXISTS student_progress;
USE student_progress;

-- -----------------------------------------
-- Table: study_logs
-- -----------------------------------------
CREATE TABLE IF NOT EXISTS study_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(100) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    hours FLOAT NOT NULL CHECK (hours >= 0),
    problems INT NOT NULL CHECK (problems >= 0),
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------
-- Indexes for faster analytics
-- -----------------------------------------
CREATE INDEX idx_subject ON study_logs(subject);
CREATE INDEX idx_date ON study_logs(date);
