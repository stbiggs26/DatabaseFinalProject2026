
// -----------------------------------------------------------------------------
// PROGRAM QUERIES - these are example queries, ideally in the application
//                    the user would be providing the data via a drop-down 
//                     of possible values.
// -----------------------------------------------------------------------------
// 1. Return all empty positions in a department and their salaries.
// -----------------------------------------------------------------------------
MATCH (job:Job {status:'Terminated'})-[:IS_IN]->(dept:Department)
RETURN job.title, job.salary, dept.name
// -----------------------------------------------------------------------------
// 2. Return every job, filled and unfilled, in a department.
// -----------------------------------------------------------------------------
MATCH (job:Job)-[:IS_IN]->(dept:Department)
RETURN job.title, job.status, dept.name
// -----------------------------------------------------------------------------
// 3. Return the skills and departments of all of the top performers in the company.
// -----------------------------------------------------------------------------
MATCH (e:Employee)-[*0..2]->(dept:Department),
      (e:Employee)-[:HAS]->(s:Skill)
      WHERE e.performance >= 5
RETURN DISTINCT s.name, dept.name
// -----------------------------------------------------------------------------
// 4. Return a pool of current and former employees, who work in a particular location, have a certain set of skills, 
//    certification and/or degree, and have a certain amount of experience.
// -----------------------------------------------------------------------------
MATCH (e:Employee) -[:EMPLOYED_IN]-> (j:Job {work_location: 'North Calvin'})-[:IS_IN]->(dept:Department),
(e:Employee) -[:HAS]->(s:Skill {name: 'Project Management'}),
(e:Employee) -[:HAS]-> (d:Degree {type: 'PhD'}),
(e:Employee) -[:HAS]-> (c:Certification {name: 'Six Sigma Green Belt'})
WHERE e.years_of_service >= 3
    AND e.`work experience` >= 10
RETURN e.first_name, e.last_name, e.status, j.title, d.name
// -----------------------------------------------------------------------------
// 5. Return the sum of salaries each department is paying to active employees and 
//    has available for open positions.
// -----------------------------------------------------------------------------
MATCH (jobActive: Job) -[:IS_IN]-> (dept:Department {name: 'Finance'}),
(jobTermed: Job {status: 'Terminated'}) -[:IS_IN]-> (dept)
WHERE jobActive.status IN ['Active', 'On Leave']
RETURN sum(jobActive.salary) AS ActiveEmployeeSalariesTotal,
        sum(jobTermed.salary) AS AvailableSalaryDollars
// -----------------------------------------------------------------------------
// 6. Return all employees in a department, their job information, and their manager.
// -----------------------------------------------------------------------------
MATCH (mgr:Employee)<-[:REPORTS_TO]-(e:Employee)-[:EMPLOYED_IN]->(j:Job)-[:IS_IN]->(dept:Department {name: 'Finance'})
WHERE e.status IN ['Active', 'On Leave']
RETURN e.employee_id AS EmployeeID, e.first_name AS EmployeeFirstName, e.last_name AS EmployeeLastName, 
        j.title AS JobTitle, e.status AS EmployeeStatus, j.employment_type AS TypeofEmployment,
        j.shift_type AS Shift, j.time_status as TimeStatus, j.salary AS Salary,
        mgr.first_name AS ManagerFirstName, mgr.last_name AS ManagerLastName
// -----------------------------------------------------------------------------
// 7. Return a list of all managers and their job titles.
// -----------------------------------------------------------------------------
MATCH (dept:Department {name: 'Finance'})<-[:IS_IN]-(j:Job)<-[:EMPLOYED_IN]-(mgr:Employee)<-[:REPORTS_TO]-(e:Employee)
RETURN DISTINCT mgr.employee_id AS EmployeeID, mgr.first_name AS FirstName, mgr.last_name AS LastName, 
        j.title AS JobTitle, COUNT(DISTINCT e.employee_id) AS NumberofDirectReports
//
//
//
// -----------------------------------------------------------------------------
// FUNCTIONAL QUERIES - used as menu options for users to choose from
// -----------------------------------------------------------------------------
// -----------------------------------------------------------------------------
// 1. Certification Options
// -----------------------------------------------------------------------------
MATCH (c:Certification)
RETURN DISTINCT c.name
// -----------------------------------------------------------------------------
// 2. Degree Options
// -----------------------------------------------------------------------------
MATCH (d:Degree)
RETURN DISTINCT d.type
// -----------------------------------------------------------------------------
// 3. Department Options
// -----------------------------------------------------------------------------
MATCH (dept:Department)
RETURN DISTINCT dept.name
// -----------------------------------------------------------------------------
// 4. Skill Options
// -----------------------------------------------------------------------------
MATCH (s:Skill)
RETURN DISTINCT s.name
// -----------------------------------------------------------------------------
// 5. Work Location Options
// -----------------------------------------------------------------------------
MATCH (j:Job)
RETURN DISTINCT j.work_location
// -----------------------------------------------------------------------------
// 6. Job/Employee Status Options
// -----------------------------------------------------------------------------
MATCH (j:Job)
RETURN DISTINCT j.status