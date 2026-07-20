from __future__ import annotations

from pathlib import Path

import pandas as pd
from shiny import App, reactive, render, ui

from neo4j_utils import clean_for_display, get_client
from queries import (
    CERTIFICATION_OPTIONS,
    DEGREE_OPTIONS,
    DEPARTMENT_BUDGET,
    DEPARTMENT_OPTIONS,
    EMPLOYEE_SEARCH,
    EMPLOYEE_STATUS_OPTIONS,
    EMPLOYEES_WITH_SKILL,
    JOBS_BY_DEPARTMENT,
    JOBS_REQUIRING_SKILL,
    LOCATION_OPTIONS,
    SKILL_OPTIONS,
    TALENT_SEARCH,
)

APP_DIR = Path(__file__).parent
EMPTY_DF = pd.DataFrame()

# User-facing job status labels. The database values stay unchanged.
POSITION_STATUS_CHOICES = {
    "": "All positions",
    "filled": "Filled",
    "Terminated": "Unfilled",
}

POSITION_STATUS_DISPLAY = {
    "Active": "Filled",
    "On Leave": "Filled - employee on leave",
    "Terminated": "Unfilled",
}


def run_query(query: str, parameters: dict | None = None) -> pd.DataFrame:
    try:
        return clean_for_display(get_client().query_df(query, parameters))
    except Exception as exc:
        ui.notification_show(
            f"The database query could not be completed: {exc}",
            type="error",
            duration=8,
        )
        return EMPTY_DF.copy()


def option_values(query: str) -> list[str]:
    df = run_query(query)
    if df.empty or "value" not in df.columns:
        return []
    return [str(value) for value in df["value"].dropna().tolist()]


app_ui = ui.page_navbar(
    ui.head_content(ui.include_css(APP_DIR / "styles.css")),
    ui.nav_panel(
        "Employees",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h5("Search filters"),
                ui.input_select("employee_department", "Department", {"": "All departments"}),
                ui.input_select("employee_status", "Employee status", {"": "All statuses"}),
                ui.input_text("employee_name", "Employee name", placeholder="First or last name"),
                ui.input_action_button("employee_search", "Search employees", class_="btn-primary w-100"),
                width=290,
            ),
            ui.card(
                ui.card_header("Employee results"),
                ui.p(
                    "Search by department, status, or name. Select filters and choose Search employees.",
                    class_="text-muted",
                ),
                ui.output_data_frame("employee_results"),
                full_screen=True,
            ),
        ),
    ),
    ui.nav_panel(
        "Jobs & Departments",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h5("Department"),
                ui.input_select("job_department", "Choose a department", []),
                ui.input_select(
                    "job_status",
                    "Position status",
                    POSITION_STATUS_CHOICES,
                ),
                ui.input_action_button("load_jobs", "Load department", class_="btn-primary w-100"),
                width=290,
            ),
            ui.layout_column_wrap(
                ui.value_box(
                    "Current salary total",
                    ui.output_text("active_salary_total"),
                    "Jobs whose status is Active or On Leave",
                    theme="primary",
                ),
                ui.value_box(
                    "Available salary dollars",
                    ui.output_text("available_salary_total"),
                    "Salary tied to unfilled positions",
                    theme="secondary",
                ),
                width=1 / 2,
            ),
            ui.card(
                ui.card_header("Department jobs"),
                ui.output_data_frame("job_results"),
                full_screen=True,
            ),
        ),
    ),
    ui.nav_panel(
        "Talent Search",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h5("Candidate filters"),
                ui.input_select("talent_location", "Work location", {"": "Any location"}),
                ui.input_selectize("talent_skills", "Required skills", [], multiple=True),
                ui.input_select("talent_certification", "Certification", {"": "Any certification"}),
                ui.input_select("talent_degree", "Degree", {"": "Any degree"}),
                ui.input_numeric("minimum_service", "Minimum years of service", value=0, min=0),
                ui.input_numeric("minimum_experience", "Minimum years of experience", value=0, min=0),
                ui.input_action_button("talent_search", "Find employees", class_="btn-primary w-100"),
                width=310,
            ),
            ui.card(
                ui.card_header("Matching current and former employees"),
                ui.p(
                    "When multiple skills are selected, an employee must have every selected skill.",
                    class_="text-muted",
                ),
                ui.output_data_frame("talent_results"),
                full_screen=True,
            ),
        ),
    ),
    ui.nav_panel(
        "Skills",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h5("Skill explorer"),
                ui.input_selectize("skill_explorer", "Choose a skill", []),
                ui.input_action_button("load_skill", "Explore skill", class_="btn-primary w-100"),
                width=290,
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Employees who have this skill"),
                    ui.output_data_frame("skill_employee_results"),
                    full_screen=True,
                ),
                ui.card(
                    ui.card_header("Jobs that require this skill"),
                    ui.output_data_frame("skill_job_results"),
                    full_screen=True,
                ),
                col_widths=(6, 6),
            ),
        ),
    ),
    title="Employment Org Design & Talent App",
    id="main_navigation",
    fillable=True,
    window_title="Employment Org Design & Talent App",
)


def server(input, output, session):
    @reactive.effect
    def load_choices():
        departments = option_values(DEPARTMENT_OPTIONS)
        statuses = option_values(EMPLOYEE_STATUS_OPTIONS)
        skills = option_values(SKILL_OPTIONS)
        certifications = option_values(CERTIFICATION_OPTIONS)
        degrees = option_values(DEGREE_OPTIONS)
        locations = option_values(LOCATION_OPTIONS)

        ui.update_select(
            "employee_department",
            choices={"": "All departments", **{value: value for value in departments}},
        )
        ui.update_select(
            "employee_status",
            choices={"": "All statuses", **{value: value for value in statuses}},
        )
        ui.update_select("job_department", choices=departments)
        ui.update_select(
            "talent_location",
            choices={"": "Any location", **{value: value for value in locations}},
        )
        ui.update_selectize("talent_skills", choices=skills, server=True)
        ui.update_select(
            "talent_certification",
            choices={"": "Any certification", **{value: value for value in certifications}},
        )
        ui.update_select(
            "talent_degree",
            choices={"": "Any degree", **{value: value for value in degrees}},
        )
        ui.update_selectize("skill_explorer", choices=skills, server=True)

    @reactive.calc
    @reactive.event(input.employee_search)
    def employee_data() -> pd.DataFrame:
        return run_query(
            EMPLOYEE_SEARCH,
            {
                "department": input.employee_department() or "",
                "employee_status": input.employee_status() or "",
                "employee_name": (input.employee_name() or "").strip(),
            },
        )

    @render.data_frame
    def employee_results():
        return render.DataGrid(employee_data(), filters=True, height="650px")

    @reactive.calc
    @reactive.event(input.load_jobs)
    def job_data() -> pd.DataFrame:
        if not input.job_department():
            return EMPTY_DF.copy()
        df = run_query(
            JOBS_BY_DEPARTMENT,
            {
                "department": input.job_department(),
                "job_status": input.job_status() or "",
            },
        )
        if "JobStatus" in df.columns:
            df["JobStatus"] = df["JobStatus"].replace(POSITION_STATUS_DISPLAY)
        return df

    @reactive.calc
    @reactive.event(input.load_jobs)
    def budget_data() -> pd.DataFrame:
        if not input.job_department():
            return EMPTY_DF.copy()
        return run_query(DEPARTMENT_BUDGET, {"department": input.job_department()})

    @render.data_frame
    def job_results():
        return render.DataGrid(job_data(), filters=True, height="560px")

    @render.text
    def active_salary_total():
        df = budget_data()
        if df.empty:
            return "$0"
        value = df.iloc[0].get("ActiveEmployeeSalariesTotal", 0) or 0
        return f"${float(value):,.0f}"

    @render.text
    def available_salary_total():
        df = budget_data()
        if df.empty:
            return "$0"
        value = df.iloc[0].get("AvailableSalaryDollars", 0) or 0
        return f"${float(value):,.0f}"

    @reactive.calc
    @reactive.event(input.talent_search)
    def talent_data() -> pd.DataFrame:
        return run_query(
            TALENT_SEARCH,
            {
                "location": input.talent_location() or "",
                "skills": list(input.talent_skills() or []),
                "certification": input.talent_certification() or "",
                "degree": input.talent_degree() or "",
                "minimum_service": input.minimum_service() or 0,
                "minimum_experience": input.minimum_experience() or 0,
            },
        )

    @render.data_frame
    def talent_results():
        return render.DataGrid(talent_data(), filters=True, height="650px")

    @reactive.calc
    @reactive.event(input.load_skill)
    def skill_employee_data() -> pd.DataFrame:
        if not input.skill_explorer():
            return EMPTY_DF.copy()
        return run_query(EMPLOYEES_WITH_SKILL, {"skill": input.skill_explorer()})

    @reactive.calc
    @reactive.event(input.load_skill)
    def skill_job_data() -> pd.DataFrame:
        if not input.skill_explorer():
            return EMPTY_DF.copy()
        return run_query(JOBS_REQUIRING_SKILL, {"skill": input.skill_explorer()})

    @render.data_frame
    def skill_employee_results():
        return render.DataGrid(skill_employee_data(), filters=True, height="600px")

    @render.data_frame
    def skill_job_results():
        return render.DataGrid(skill_job_data(), filters=True, height="600px")


app = App(app_ui, server)
