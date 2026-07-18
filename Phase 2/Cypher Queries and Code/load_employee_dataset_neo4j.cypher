// Cypher to load dataset and create database from employee dataset
// Cleaned dataset in: https://raw.githubusercontent.com/stbiggs26/DatabaseFinalProject2026/refs/heads/main/employee_data_cleaned.csv
// Sourced from Kaggle
// Code based on code provided in LinkedIn Learning documentation in this github: https://github.com/LinkedInLearning/learning-neo4j-2483130/blob/main/course_material/03_01.txt
//
// -----------------------------------------------------------------------------
// 1. Add uniqueness constraints
// -----------------------------------------------------------------------------
CREATE CONSTRAINT employee_id_unique IF NOT EXISTS
FOR (employee:Employee) REQUIRE employee.employee_id IS UNIQUE;

CREATE CONSTRAINT job_position_id_unique IF NOT EXISTS
FOR (job:Job) REQUIRE job.position_id IS UNIQUE;

CREATE CONSTRAINT department_name_unique IF NOT EXISTS
FOR (department:Department) REQUIRE department.name IS UNIQUE;

CREATE CONSTRAINT degree_type_unique IF NOT EXISTS
FOR (degree:Degree) REQUIRE degree.type IS UNIQUE;

CREATE CONSTRAINT skill_name_unique IF NOT EXISTS
FOR (skill:Skill) REQUIRE skill.name IS UNIQUE;

CREATE CONSTRAINT certification_name_unique IF NOT EXISTS
FOR (certification:Certification) REQUIRE certification.name IS UNIQUE;

// -----------------------------------------------------------------------------
// 2. Load Employee nodes
// -----------------------------------------------------------------------------
LOAD CSV WITH HEADERS FROM
"https://raw.githubusercontent.com/stbiggs26/DatabaseFinalProject2026/refs/heads/main/employee_data_cleaned.csv" AS row
WITH row, split(trim(row.date_of_birth), '/') AS dobParts
MERGE (employee:Employee {employee_id: trim(row.employee_id)})
SET employee.original_employee_id = trim(row.original_employee_id),
    employee.first_name = trim(row.first_name),
    employee.last_name = trim(row.last_name),
    employee.status = trim(row.employee_status),
    employee.gender = trim(row.gender),
    employee.date_of_birth = CASE
        WHEN row.date_of_birth IS NULL OR trim(row.date_of_birth) = '' THEN null
        ELSE date({
            year: toInteger(dobParts[2]),
            month: toInteger(dobParts[0]),
            day: toInteger(dobParts[1])
        })
    END,
    employee.performance = CASE
        WHEN row.performance_rating IS NULL OR trim(row.performance_rating) = '' THEN null
        ELSE toInteger(row.performance_rating)
    END;


// -----------------------------------------------------------------------------
// 3. Create one Job/position per employee and connect through EMPLOYED_IN
//    position_id uses employee_id.
// -----------------------------------------------------------------------------
LOAD CSV WITH HEADERS FROM
"https://raw.githubusercontent.com/stbiggs26/DatabaseFinalProject2026/refs/heads/main/employee_data_cleaned.csv" AS row
WITH row,
     split(trim(row.hire_date), '/') AS hireParts,
     CASE
         WHEN row.termination_date IS NULL OR trim(row.termination_date) = ''
         THEN null
         ELSE split(trim(row.termination_date), '/')
     END AS terminationParts
MATCH (employee:Employee {employee_id: trim(row.employee_id)})
MERGE (job:Job {position_id: trim(row.employee_id)})
SET job.title = trim(row.job_title),
    job.salary = CASE
        WHEN row.salary IS NULL OR trim(row.salary) = '' THEN null
        ELSE toInteger(row.salary)
    END,
    job.time_status = trim(row.employment_status),
    job.employment_type = trim(row.employee_type),
    job.shift_type = trim(row.work_shift),
    job.status = trim(row.employee_status),
    job.work_location = trim(row.work_location)
MERGE (employee)-[employment:EMPLOYED_IN]->(job)
SET employment.start_date = CASE
        WHEN row.hire_date IS NULL OR trim(row.hire_date) = '' THEN null
        ELSE date({
            year: toInteger(hireParts[2]),
            month: toInteger(hireParts[0]),
            day: toInteger(hireParts[1])
        })
    END,
    employment.termination_date = CASE
        WHEN terminationParts IS NULL THEN null
        ELSE date({
            year: toInteger(terminationParts[2]),
            month: toInteger(terminationParts[0]),
            day: toInteger(terminationParts[1])
        })
    END;

// -----------------------------------------------------------------------------
// 4. Create Department nodes and connect Job via IS_IN Department
// -----------------------------------------------------------------------------
LOAD CSV WITH HEADERS FROM
"https://raw.githubusercontent.com/stbiggs26/DatabaseFinalProject2026/refs/heads/main/employee_data_cleaned.csv" AS row
WITH row, trim(row.department) AS departmentName
WHERE departmentName <> ''
MATCH (job:Job {position_id: trim(row.employee_id)})
MERGE (department:Department {name: departmentName})
MERGE (job)-[:IS_IN]->(department);

// -----------------------------------------------------------------------------
// 5. Create Degree nodes and connect Employee via HAS Degree
// -----------------------------------------------------------------------------
LOAD CSV WITH HEADERS FROM
"https://raw.githubusercontent.com/stbiggs26/DatabaseFinalProject2026/refs/heads/main/employee_data_cleaned.csv" AS row
WITH row, trim(row.education_level) AS degreeType
WHERE degreeType <> '' AND toLower(degreeType) <> 'none'
MATCH (employee:Employee {employee_id: trim(row.employee_id)})
MERGE (degree:Degree {type: degreeType})
MERGE (employee)-[:HAS]->(degree);

// -----------------------------------------------------------------------------
// 6. Degree requirement connected to job as well (using employee education level)
// -----------------------------------------------------------------------------
LOAD CSV WITH HEADERS FROM
"https://raw.githubusercontent.com/stbiggs26/DatabaseFinalProject2026/refs/heads/main/employee_data_cleaned.csv" AS row
WITH row, trim(row.education_level) AS degreeType
WHERE degreeType <> '' AND toLower(degreeType) <> 'none'
MATCH (job:Job {position_id: trim(row.employee_id)})
MERGE (degree:Degree {type: degreeType})
MERGE (job)-[:REQUIRES]->(degree);

// -----------------------------------------------------------------------------
// 7. Create required Skill nodes and connect Job via REQUIRES Skill
// -----------------------------------------------------------------------------
LOAD CSV WITH HEADERS FROM
"https://raw.githubusercontent.com/stbiggs26/DatabaseFinalProject2026/refs/heads/main/employee_data_cleaned.csv" AS row
MATCH (job:Job {position_id: trim(row.employee_id)})
UNWIND split(coalesce(row.job_required_skills, ''), '|') AS rawSkillName
WITH job, trim(rawSkillName) AS skillName
WHERE skillName <> '' AND toLower(skillName) <> 'none'
MERGE (skill:Skill {name: skillName})
MERGE (job)-[:REQUIRES]->(skill);

// -----------------------------------------------------------------------------
// 8. Connect Employee via HAS Skill
// -----------------------------------------------------------------------------
LOAD CSV WITH HEADERS FROM
"https://raw.githubusercontent.com/stbiggs26/DatabaseFinalProject2026/refs/heads/main/employee_data_cleaned.csv" AS row
MATCH (employee:Employee {employee_id: trim(row.employee_id)})
UNWIND split(coalesce(row.employee_skills, ''), '|') AS rawSkillName
WITH employee, trim(rawSkillName) AS skillName
WHERE skillName <> '' AND toLower(skillName) <> 'none'
MERGE (skill:Skill {name: skillName})
MERGE (employee)-[:HAS]->(skill);

// -----------------------------------------------------------------------------
// 9. Create required Certification nodes and connect Job via REQUIRES Certification
// -----------------------------------------------------------------------------
LOAD CSV WITH HEADERS FROM
"https://raw.githubusercontent.com/stbiggs26/DatabaseFinalProject2026/refs/heads/main/employee_data_cleaned.csv" AS row
WITH row, trim(coalesce(row.job_required_certification, '')) AS certificationName
WHERE certificationName <> '' AND toLower(certificationName) <> 'none'
MATCH (job:Job {position_id: trim(row.employee_id)})
MERGE (certification:Certification {name: certificationName})
MERGE (job)-[:REQUIRES]->(certification);

// -----------------------------------------------------------------------------
// 10. Connect Employee via HAS Certification
// -----------------------------------------------------------------------------
LOAD CSV WITH HEADERS FROM
"https://raw.githubusercontent.com/stbiggs26/DatabaseFinalProject2026/refs/heads/main/employee_data_cleaned.csv" AS row
WITH row, trim(coalesce(row.employee_certification, '')) AS certificationName
WHERE certificationName <> '' AND toLower(certificationName) <> 'none'
MATCH (employee:Employee {employee_id: trim(row.employee_id)})
MERGE (certification:Certification {name: certificationName})
MERGE (employee)-[:HAS]->(certification);

// -----------------------------------------------------------------------------
// 11. Create Employee via REPORTS_TO Employee for manager relationships (via a matched Employee employee_id)
// -----------------------------------------------------------------------------
LOAD CSV WITH HEADERS FROM
"https://raw.githubusercontent.com/stbiggs26/DatabaseFinalProject2026/refs/heads/main/employee_data_cleaned.csv" AS row
WITH row
WHERE row.manager_id IS NOT NULL
  AND trim(row.manager_id) <> ''
  AND trim(row.manager_id) <> trim(row.employee_id)
MATCH (employee:Employee {employee_id: trim(row.employee_id)})
MATCH (manager:Employee {employee_id: trim(row.manager_id)})
MERGE (employee)-[:REPORTS_TO]->(manager);

// -----------------------------------------------------------------------------
// Additional Steps (as needed)
// -----------------------------------------------------------------------------
// Adding missing features

LOAD CSV WITH HEADERS FROM
"https://raw.githubusercontent.com/stbiggs26/DatabaseFinalProject2026/refs/heads/main/employee_data_cleaned.csv"
AS row
MATCH (employee:Employee {
    employee_id: trim(row.employee_id)})
SET employee.years_of_service = toFloat(row.years_of_service),
employee.`work experience` = toInteger(row.estimated_work_experience_years);
