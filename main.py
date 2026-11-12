"""CHEMCalc: a stoichiometry study site built with Drafter.

Calculators: percent yield, limiting reactant, theoretical yield.
Also has a formula reference page and a filterable calculation history.
"""
from drafter import *
from dataclasses import dataclass

# Global constants are allowed (they are never changed).
HISTORY_FILTERS = ["All", "Percent Yield", "Limiting Reactant",
                   "Theoretical Yield"]
BAD_INPUT_MESSAGE = ("Please enter positive numbers only (no letters or "
                     "negative signs) in every box.")


@dataclass
class Calculation:
    """One saved calculation shown on the history page.

    Attributes:
        calculation_type (str): Kind of calculation, such as "Percent Yield".
        result (float): The numerical answer of the calculation.
        description (str): Short explanation of the values that were used.
    """
    calculation_type: str
    result: float
    description: str


@dataclass
class State:
    """Everything CHEMCalc remembers while the student uses the site.

    Attributes:
        actual_yield (float): Last actual yield entered, in grams.
        theoretical_yield (float): Last theoretical yield, in grams.
        limiting_reactant (str): Name of the last limiting reactant found.
        calculations (list[Calculation]): History of saved calculations.
        current_page (str): Name of the page the student is on.
    """
    actual_yield: float
    theoretical_yield: float
    limiting_reactant: str
    calculations: list[Calculation]
    current_page: str


# ---------------------------------------------------------------------------
# Helper functions (no routes here, so they are easy to unit test)
# ---------------------------------------------------------------------------

def is_positive_number(text: str) -> bool:
    """Check whether a string is a number greater than zero, like '2.5'.

    Args:
        text (str): The text typed into a box by the student.

    Returns:
        bool: True if text is a positive number, otherwise False.
    """
    cleaned = text.strip()
    # Allow one decimal point by removing it before checking the digits.
    if not cleaned.replace(".", "", 1).isdigit():
        return False
    return float(cleaned) > 0


def all_positive_numbers(texts: list[str]) -> bool:
    """Check that every string in a list is a positive number.

    Args:
        texts (list[str]): The texts typed into the boxes.

    Returns:
        bool: True only if every string is a positive number.
    """
    for text in texts:
        if not is_positive_number(text):
            return False
    return True


def compute_percent_yield(actual: float, theoretical: float) -> float:
    """Calculate percent yield as actual / theoretical * 100.

    Args:
        actual (float): Actual yield in grams.
        theoretical (float): Theoretical yield in grams (not zero).

    Returns:
        float: The percent yield, rounded to 2 decimal places.
    """
    return round(actual / theoretical * 100, 2)


def find_limiting_reactant(name_one: str, moles_one: float, coeff_one: float,
                           name_two: str, moles_two: float,
                           coeff_two: float) -> str:
    """Find which of two reactants runs out first.

    The limiting reactant has the smaller moles / coefficient ratio.

    Args:
        name_one (str): Name of the first reactant.
        moles_one (float): Moles of the first reactant available.
        coeff_one (float): Coefficient of the first reactant.
        name_two (str): Name of the second reactant.
        moles_two (float): Moles of the second reactant available.
        coeff_two (float): Coefficient of the second reactant.

    Returns:
        str: The name of the limiting reactant (the first one if tied).
    """
    ratio_one = moles_one / coeff_one
    ratio_two = moles_two / coeff_two
    if ratio_one <= ratio_two:
        return name_one
    return name_two


def smallest_ratio(moles_one: float, coeff_one: float,
                   moles_two: float, coeff_two: float) -> float:
    """Find the smaller of the two moles / coefficient ratios.

    Args:
        moles_one (float): Moles of the first reactant.
        coeff_one (float): Coefficient of the first reactant.
        moles_two (float): Moles of the second reactant.
        coeff_two (float): Coefficient of the second reactant.

    Returns:
        float: The smaller ratio, rounded to 3 decimal places.
    """
    ratio_one = moles_one / coeff_one
    ratio_two = moles_two / coeff_two
    if ratio_one <= ratio_two:
        return round(ratio_one, 3)
    return round(ratio_two, 3)


def compute_theoretical_yield(mass: float, molar_mass: float,
                              reactant_coeff: float, product_coeff: float,
                              product_molar_mass: float) -> float:
    """Calculate theoretical yield of product from the limiting reactant.

    Steps: grams reactant -> moles reactant -> moles product -> grams product.

    Args:
        mass (float): Mass of the limiting reactant in grams.
        molar_mass (float): Molar mass of the limiting reactant in g/mol.
        reactant_coeff (float): Coefficient of the limiting reactant.
        product_coeff (float): Coefficient of the product.
        product_molar_mass (float): Molar mass of the product in g/mol.

    Returns:
        float: Theoretical yield in grams, rounded to 2 decimal places.
    """
    moles_reactant = mass / molar_mass
    moles_product = moles_reactant * product_coeff / reactant_coeff
    return round(moles_product * product_molar_mass, 2)


def add_calculation(state: State, calculation_type: str, result: float,
                    description: str) -> None:
    """Save a new Calculation at the end of the history list.

    Args:
        state (State): The current state, whose list is changed.
        calculation_type (str): Kind of calculation that was done.
        result (float): The numerical answer.
        description (str): Short explanation of the values used.

    Returns:
        None: The state's calculations list is modified in place.
    """
    state.calculations.append(
        Calculation(calculation_type, result, description))


def history_lines(calculations: list[Calculation],
                  chosen_type: str) -> list[str]:
    """Build one line of text for each calculation that matches a filter.

    Args:
        calculations (list[Calculation]): The saved calculations.
        chosen_type (str): A calculation type, or "All" to keep everything.

    Returns:
        list[str]: Text lines like "Percent Yield: 50.0 (description)".
    """
    lines = []
    for calculation in calculations:
        if chosen_type == "All" or calculation.calculation_type == chosen_type:
            lines.append(calculation.calculation_type + ": "
                         + str(calculation.result) + " ("
                         + calculation.description + ")")
    return lines


def page_buttons() -> list:
    """Make the buttons that link to every page except Home.

    Returns:
        list: Five Drafter Button components.
    """
    return [Button("Percent Yield", percent_yield),
            Button("Limiting Reactant", limiting_reactant),
            Button("Theoretical Yield", theoretical_yield),
            Button("Formulas", formula_reference),
            Button("History", history)]


def nav_buttons() -> list:
    """Make the navigation row for every page except the home page.

    Returns:
        list: A Home button followed by the buttons from page_buttons().
    """
    return [Button("Home", index)] + page_buttons()


def error_page(state: State, back_route) -> Page:
    """Make a page telling the student their input was not valid.

    Args:
        state (State): The current state (not changed).
        back_route: The route function the Go Back button returns to.

    Returns:
        Page: An error page with a Go Back button and navigation.
    """
    return Page(state, [Header("Oops!"), BAD_INPUT_MESSAGE, LineBreak(),
                        Button("Go Back", back_route)] + nav_buttons())


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@route
def index(state: State) -> Page:
    """Show the home page. (Drafter starts on a route named index.)

    Args:
        state (State): The current state; current_page is updated.

    Returns:
        Page: The home page with buttons to every other page.
    """
    state.current_page = "Home"
    return Page(state, [
        Header("CHEMCalc"),
        "A study helper for stoichiometry. Pick a tool below.",
        LineBreak(),
        "You have saved " + str(len(state.calculations)) + " calculation(s).",
        LineBreak()] + page_buttons())


@route
def percent_yield(state: State) -> Page:
    """Show the percent yield input page.

    Args:
        state (State): The current state; current_page is updated.

    Returns:
        Page: A page with boxes for actual and theoretical yield.
    """
    state.current_page = "Percent Yield"
    return Page(state, [
        Header("Percent Yield Calculator"),
        "Actual yield (g):", TextBox("actual", "0"), LineBreak(),
        "Theoretical yield (g):", TextBox("theoretical", "0"), LineBreak(),
        Button("Calculate", calculate_percent_yield), LineBreak()]
        + nav_buttons())


@route
def calculate_percent_yield(state: State, actual: str,
                            theoretical: str) -> Page:
    """Calculate percent yield and save it to the history.

    Args:
        state (State): The current state; yields and history are updated.
        actual (str): Text from the actual yield box.
        theoretical (str): Text from the theoretical yield box.

    Returns:
        Page: The result page, or an error page if the input is invalid.
    """
    if not all_positive_numbers([actual, theoretical]):
        return error_page(state, percent_yield)
    state.actual_yield = float(actual)
    state.theoretical_yield = float(theoretical)
    result = compute_percent_yield(state.actual_yield,
                                   state.theoretical_yield)
    description = (actual + " g actual / " + theoretical
                   + " g theoretical")
    add_calculation(state, "Percent Yield", result, description)
    message = "Percent yield = " + str(result) + "%"
    if result > 100:
        message += " (over 100%, so check for impurities or a mistake)"
    return Page(state, [Header("Result"), message, LineBreak(),
                        Button("Another Calculation", percent_yield)]
                + nav_buttons())


@route
def limiting_reactant(state: State) -> Page:
    """Show the limiting reactant input page.

    Args:
        state (State): The current state; current_page is updated.

    Returns:
        Page: A page with boxes for two reactants' names, moles and
            coefficients.
    """
    state.current_page = "Limiting Reactant"
    return Page(state, [
        Header("Limiting Reactant Calculator"),
        "Amounts are in moles. Coefficients come from the balanced equation.",
        LineBreak(),
        "Reactant 1 name:", TextBox("name_one", "H2"), LineBreak(),
        "Reactant 1 moles:", TextBox("moles_one", "0"), LineBreak(),
        "Reactant 1 coefficient:", TextBox("coeff_one", "2"), LineBreak(),
        "Reactant 2 name:", TextBox("name_two", "O2"), LineBreak(),
        "Reactant 2 moles:", TextBox("moles_two", "0"), LineBreak(),
        "Reactant 2 coefficient:", TextBox("coeff_two", "1"), LineBreak(),
        Button("Find Limiting Reactant", calculate_limiting_reactant),
        LineBreak()] + nav_buttons())


@route
def calculate_limiting_reactant(state: State, name_one: str, moles_one: str,
                                coeff_one: str, name_two: str,
                                moles_two: str, coeff_two: str) -> Page:
    """Find the limiting reactant and save it to the history.

    Args:
        state (State): The current state; limiting_reactant and history
            are updated.
        name_one (str): Text from the first reactant's name box.
        moles_one (str): Text from the first reactant's moles box.
        coeff_one (str): Text from the first reactant's coefficient box.
        name_two (str): Text from the second reactant's name box.
        moles_two (str): Text from the second reactant's moles box.
        coeff_two (str): Text from the second reactant's coefficient box.

    Returns:
        Page: The result page, or an error page if the input is invalid.
    """
    numbers = [moles_one, coeff_one, moles_two, coeff_two]
    if not all_positive_numbers(numbers):
        return error_page(state, limiting_reactant)
    if name_one.strip() == "" or name_two.strip() == "":
        return error_page(state, limiting_reactant)
    state.limiting_reactant = find_limiting_reactant(
        name_one.strip(), float(moles_one), float(coeff_one),
        name_two.strip(), float(moles_two), float(coeff_two))
    ratio = smallest_ratio(float(moles_one), float(coeff_one),
                           float(moles_two), float(coeff_two))
    description = ("limiting reactant is " + state.limiting_reactant
                   + "; smallest moles/coefficient ratio shown as result")
    add_calculation(state, "Limiting Reactant", ratio, description)
    return Page(state, [
        Header("Result"),
        "The limiting reactant is " + state.limiting_reactant + ".",
        LineBreak(),
        Button("Another Calculation", limiting_reactant)] + nav_buttons())


@route
def theoretical_yield(state: State) -> Page:
    """Show the theoretical yield input page.

    Args:
        state (State): The current state; current_page is updated.

    Returns:
        Page: A page with boxes for the limiting reactant and product data.
    """
    state.current_page = "Theoretical Yield"
    hint = "Last limiting reactant found: " + state.limiting_reactant
    return Page(state, [
        Header("Theoretical Yield Calculator"), hint, LineBreak(),
        "Limiting reactant mass (g):", TextBox("mass", "0"), LineBreak(),
        "Limiting reactant molar mass (g/mol):",
        TextBox("molar_mass", "0"), LineBreak(),
        "Limiting reactant coefficient:",
        TextBox("reactant_coeff", "1"), LineBreak(),
        "Product coefficient:", TextBox("product_coeff", "1"), LineBreak(),
        "Product molar mass (g/mol):",
        TextBox("product_molar_mass", "0"), LineBreak(),
        Button("Calculate", calculate_theoretical_yield), LineBreak()]
        + nav_buttons())


@route
def calculate_theoretical_yield(state: State, mass: str, molar_mass: str,
                                reactant_coeff: str, product_coeff: str,
                                product_molar_mass: str) -> Page:
    """Calculate theoretical yield and save it to the history.

    Args:
        state (State): The current state; theoretical_yield and history
            are updated.
        mass (str): Text from the limiting reactant mass box.
        molar_mass (str): Text from the limiting reactant molar mass box.
        reactant_coeff (str): Text from the reactant coefficient box.
        product_coeff (str): Text from the product coefficient box.
        product_molar_mass (str): Text from the product molar mass box.

    Returns:
        Page: The result page, or an error page if the input is invalid.
    """
    numbers = [mass, molar_mass, reactant_coeff, product_coeff,
               product_molar_mass]
    if not all_positive_numbers(numbers):
        return error_page(state, theoretical_yield)
    state.theoretical_yield = compute_theoretical_yield(
        float(mass), float(molar_mass), float(reactant_coeff),
        float(product_coeff), float(product_molar_mass))
    description = (mass + " g of " + state.limiting_reactant
                   + " used as the limiting reactant")
    add_calculation(state, "Theoretical Yield", state.theoretical_yield,
                    description)
    return Page(state, [
        Header("Result"),
        "Theoretical yield = " + str(state.theoretical_yield) + " g",
        LineBreak(),
        Button("Another Calculation", theoretical_yield)] + nav_buttons())


@route
def formula_reference(state: State) -> Page:
    """Show the formula reference page.

    Args:
        state (State): The current state; current_page is updated.

    Returns:
        Page: A page listing the chemistry formulas used on the site.
    """
    state.current_page = "Formulas"
    return Page(state, [
        Header("Formula Reference"),
        BulletedList([
            "Percent yield = (actual yield / theoretical yield) x 100",
            "Moles = mass (g) / molar mass (g/mol)",
            "Limiting reactant: divide each reactant's moles by its "
            "coefficient; the smaller ratio is limiting",
            "Theoretical yield (g) = moles of limiting reactant x "
            "(product coefficient / reactant coefficient) x "
            "product molar mass"]),
        LineBreak()] + nav_buttons())


@route
def history(state: State) -> Page:
    """Show every saved calculation, with a filter box.

    Args:
        state (State): The current state; current_page is updated.

    Returns:
        Page: The history page showing all saved calculations.
    """
    state.current_page = "History"
    return history_page(state, "All")


@route
def filter_history(state: State, chosen_type: str) -> Page:
    """Show only the saved calculations of the chosen type.

    Args:
        state (State): The current state (not changed).
        chosen_type (str): The type picked in the select box.

    Returns:
        Page: The history page filtered to chosen_type.
    """
    return history_page(state, chosen_type)


def history_page(state: State, chosen_type: str) -> Page:
    """Build the history page for the chosen filter.

    Args:
        state (State): The current state holding the saved calculations.
        chosen_type (str): A calculation type, or "All".

    Returns:
        Page: The history page with the matching calculations listed.
    """
    lines = history_lines(state.calculations, chosen_type)
    if len(lines) == 0:
        body = ["No calculations to show yet."]
    else:
        body = [BulletedList(lines)]
    return Page(state, [
        Header("Calculation History"),
        "Show:", SelectBox("chosen_type", HISTORY_FILTERS, chosen_type),
        Button("Filter", filter_history), LineBreak()]
        + body + [LineBreak()] + nav_buttons())


# ---------------------------------------------------------------------------
# Unit tests (each route has at least one; they check the returned state)
# ---------------------------------------------------------------------------

def blank_state() -> State:
    """Make a fresh State used by the tests and by the site.

    Returns:
        State: A state with zero yields, no history and the Home page.
    """
    return State(0.0, 0.0, "None yet", [], "Home")


assert_equal(is_positive_number("2.5"), True)
assert_equal(is_positive_number("-3"), False)
assert_equal(is_positive_number("abc"), False)
assert_equal(all_positive_numbers(["1", "2"]), True)
assert_equal(all_positive_numbers(["1", "x"]), False)
assert_equal(compute_percent_yield(5.0, 10.0), 50.0)
assert_equal(find_limiting_reactant("H2", 4.0, 2.0, "O2", 1.0, 1.0), "O2")
assert_equal(find_limiting_reactant("H2", 1.0, 2.0, "O2", 5.0, 1.0), "H2")
assert_equal(smallest_ratio(4.0, 2.0, 1.0, 1.0), 1.0)
assert_equal(compute_theoretical_yield(4.0, 2.0, 2.0, 2.0, 18.0), 36.0)
assert_equal(history_lines([Calculation("Percent Yield", 50.0, "x")],
                           "Theoretical Yield"), [])
assert_equal(history_lines([Calculation("Percent Yield", 50.0, "x")],
                           "All"), ["Percent Yield: 50.0 (x)"])

# index
assert_equal(index(blank_state()).state.current_page, "Home")
# percent_yield
assert_equal(percent_yield(blank_state()).state.current_page,
             "Percent Yield")
# calculate_percent_yield
assert_equal(calculate_percent_yield(blank_state(), "5", "10")
             .state.calculations,
             [Calculation("Percent Yield", 50.0,
                          "5 g actual / 10 g theoretical")])
assert_equal(calculate_percent_yield(blank_state(), "x", "10")
             .state.calculations, [])
# limiting_reactant
assert_equal(limiting_reactant(blank_state()).state.current_page,
             "Limiting Reactant")
# calculate_limiting_reactant
assert_equal(calculate_limiting_reactant(blank_state(), "H2", "4", "2",
                                         "O2", "1", "1")
             .state.limiting_reactant, "O2")
# theoretical_yield
assert_equal(theoretical_yield(blank_state()).state.current_page,
             "Theoretical Yield")
# calculate_theoretical_yield
assert_equal(calculate_theoretical_yield(blank_state(), "4", "2", "2", "2",
                                         "18").state.theoretical_yield, 36.0)
# formula_reference
assert_equal(formula_reference(blank_state()).state.current_page, "Formulas")
# history
assert_equal(history(blank_state()).state.current_page, "History")
# filter_history
assert_equal(filter_history(blank_state(), "Percent Yield")
             .state.calculations, [])

start_server(blank_state())
