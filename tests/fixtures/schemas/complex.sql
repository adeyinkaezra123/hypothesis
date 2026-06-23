-- PostgreSQL fixture: self-referential FK, circular dependency, and a
-- many-to-many junction table.

-- Self-referential: employees.manager_id -> employees.id
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    manager_id INTEGER REFERENCES employees(id),
    department VARCHAR(100),
    hired_at DATE NOT NULL DEFAULT CURRENT_DATE
);

-- Circular: authors.featured_book_id <-> books.author_id.
-- featured_book_id is nullable so the cycle can be broken on insert.
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    featured_book_id INTEGER
);

CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author_id INTEGER NOT NULL REFERENCES authors(id)
);

ALTER TABLE authors
    ADD CONSTRAINT fk_authors_featured_book
    FOREIGN KEY (featured_book_id) REFERENCES books(id);

-- Many-to-many: students <-> courses via the enrollments junction table.
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL
);

CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL
);

CREATE TABLE enrollments (
    student_id INTEGER NOT NULL REFERENCES students(id),
    course_id INTEGER NOT NULL REFERENCES courses(id),
    enrolled_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (student_id, course_id)
);
