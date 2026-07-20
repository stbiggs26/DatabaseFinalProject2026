# All user-entered values are supplied as Cypher parameters. Do not insert user
# input into query strings with f-strings or string concatenation.

DEPARTMENT_OPTIONS = """
MATCH (dept:Department)
WHERE dept.name IS NOT NULL
RETURN DISTINCT dept.name AS value
ORDER BY value
"""

EMPLOYEE_STATUS_OPTIONS = """
MATCH (e:Employee)
WHERE e.status IS NOT NULL
RETURN DISTINCT e.status AS value
ORDER BY value
"""

SKILL_OPTIONS = """
MATCH (s:Skill)
WHERE s.name IS NOT NULL
RETURN DISTINCT s.name AS value
ORDER BY value
"""

CERTIFICATION_OPTIONS = """
MATCH (c:Certification)
WHERE c.name IS NOT NULL
RETURN DISTINCT c.name AS value
ORDER BY value
"""

DEGREE_OPTIONS = """
MATCH (d:Degree)
WHERE d.type IS NOT NULL
RETURN DISTINCT d.type AS value
ORDER BY value
"""

LOCATION_OPTIONS = """
MATCH (j:Job)
WHERE j.work_location IS NOT NULL
RETURN DISTINCT j.work_location AS value
ORDER BY value
"""

EMPLOYEE_SEARCH = """
MATCH (e:Employee)-[:EMPLOYED_IN]->(j:Job)-[:IS_IN]->(dept:Department)
WHERE ($department = '' OR dept.name = $department)
  AND ($employee_status = '' OR e.status = $employee_status)
  AND (
        $employee_name = ''
        OR toLower(e.first_name + ' ' + e.last_name)
           CONTAINS toLower($employee_name)
      )
OPTIONAL MATCH (e)-[:REPORTS_TO]->(mgr:Employee)
OPTIONAL MATCH (e)-[:HAS]->(skill:Skill)
RETURN
    e.employee_id AS EmployeeID,
    e.first_name AS FirstName,
    e.last_name AS LastName,
    e.status AS EmployeeStatus,
    e.performance AS Performance,
    e.years_of_service AS YearsOfService,
    e.`work experience` AS WorkExperience,
    j.position_id AS PositionID,
    j.title AS JobTitle,
    dept.name AS Department,
    j.work_location AS WorkLocation,
    j.salary AS Salary,
    mgr.first_name + ' ' + mgr.last_name AS Manager,
    collect(DISTINCT skill.name) AS Skills
ORDER BY LastName, FirstName
"""

JOBS_BY_DEPARTMENT = """
MATCH (j:Job)-[:IS_IN]->(dept:Department)
WHERE dept.name = $department
  AND (
        $job_status = ''
        OR ($job_status = 'filled' AND j.status IN ['Active', 'On Leave'])
        OR j.status = $job_status
      )
OPTIONAL MATCH (e:Employee)-[:EMPLOYED_IN]->(j)
WHERE e.status IN ['Active', 'On Leave']
RETURN
    j.position_id AS PositionID,
    j.title AS JobTitle,
    j.status AS JobStatus,
    j.salary AS Salary,
    j.employment_type AS EmploymentType,
    j.time_status AS TimeStatus,
    j.shift_type AS Shift,
    j.work_location AS WorkLocation,
    head(collect(DISTINCT e.first_name + ' ' + e.last_name)) AS CurrentEmployee
ORDER BY JobTitle, PositionID
"""

DEPARTMENT_BUDGET = """
MATCH (j:Job)-[:IS_IN]->(dept:Department)
WHERE dept.name = $department
RETURN
    sum(
        CASE WHEN j.status IN ['Active', 'On Leave']
        THEN coalesce(j.salary, 0) ELSE 0 END
    ) AS ActiveEmployeeSalariesTotal,
    sum(
        CASE WHEN j.status = 'Terminated'
        THEN coalesce(j.salary, 0) ELSE 0 END
    ) AS AvailableSalaryDollars
"""

TALENT_SEARCH = """
MATCH (e:Employee)-[:EMPLOYED_IN]->(j:Job)-[:IS_IN]->(dept:Department)
WHERE ($location = '' OR j.work_location = $location)
  AND coalesce(e.years_of_service, 0) >= $minimum_service
  AND coalesce(e.`work experience`, 0) >= $minimum_experience
  AND (
        $degree = ''
        OR EXISTS {
            MATCH (e)-[:HAS]->(degree:Degree)
            WHERE degree.type = $degree
        }
      )
  AND (
        $certification = ''
        OR EXISTS {
            MATCH (e)-[:HAS]->(cert:Certification)
            WHERE cert.name = $certification
        }
      )
  AND (
        size($skills) = 0
        OR ALL(skill_name IN $skills WHERE EXISTS {
            MATCH (e)-[:HAS]->(skill:Skill)
            WHERE skill.name = skill_name
        })
      )
OPTIONAL MATCH (e)-[:HAS]->(employee_skill:Skill)
OPTIONAL MATCH (e)-[:HAS]->(employee_cert:Certification)
OPTIONAL MATCH (e)-[:HAS]->(employee_degree:Degree)
RETURN
    e.employee_id AS EmployeeID,
    e.first_name AS FirstName,
    e.last_name AS LastName,
    e.status AS EmployeeStatus,
    j.title AS CurrentOrFormerJob,
    dept.name AS Department,
    j.work_location AS WorkLocation,
    e.years_of_service AS YearsOfService,
    e.`work experience` AS WorkExperience,
    collect(DISTINCT employee_skill.name) AS Skills,
    collect(DISTINCT employee_cert.name) AS Certifications,
    collect(DISTINCT employee_degree.type) AS Degrees
ORDER BY LastName, FirstName
"""

EMPLOYEES_WITH_SKILL = """
MATCH (e:Employee)-[:HAS]->(s:Skill {name: $skill})
OPTIONAL MATCH (e)-[:EMPLOYED_IN]->(j:Job)-[:IS_IN]->(dept:Department)
RETURN DISTINCT
    e.employee_id AS EmployeeID,
    e.first_name AS FirstName,
    e.last_name AS LastName,
    e.status AS EmployeeStatus,
    j.title AS JobTitle,
    dept.name AS Department
ORDER BY LastName, FirstName
"""

JOBS_REQUIRING_SKILL = """
MATCH (j:Job)-[:REQUIRES]->(s:Skill {name: $skill})
OPTIONAL MATCH (j)-[:IS_IN]->(dept:Department)
RETURN DISTINCT
    j.position_id AS PositionID,
    j.title AS JobTitle,
    j.status AS JobStatus,
    dept.name AS Department,
    j.salary AS Salary,
    j.work_location AS WorkLocation
ORDER BY JobTitle, PositionID
"""
