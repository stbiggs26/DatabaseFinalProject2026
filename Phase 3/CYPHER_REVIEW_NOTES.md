# Cypher review notes

The starter app preserves the intent of the submitted queries while making the following corrections:

1. **Parameters:** Department, location, skill, degree, certification, name, and experience values are passed as Cypher parameters rather than inserted into query strings.
2. **Top performers:** An explicit Employee -> Job -> Department path is safer than `[*0..2]`, which can traverse unintended relationship types.
3. **Degree property:** The schema defines the Degree identifier as `type`, so queries return `degree.type`, not `degree.name`.
4. **Flexible talent search:** Degree and certification filters are optional, and a user may select zero or more skills.
5. **Salary totals:** Conditional aggregation avoids the Cartesian multiplication caused by matching active and terminated jobs in the same query pattern.
6. **Managers:** `OPTIONAL MATCH` keeps employees whose manager relationship is missing, including top-level managers.
7. **Dropdowns:** Option queries remove nulls, use aliases, and sort results.
