from radon import metrics
from radon.raw import analyze


def create_complexity_metrics(code_snippet):

    # Analyze a single code snippet
    results = analyze(code_snippet)

    """Given a source code snippet, compute the necessary parameters to compute the Maintainability Index metric. 
    These include:
    the Halstead Volume
    the Cyclomatic Complexity
    the number of LLOC (Logical Lines of Code)
    the percent of lines of comment
    Parameters:	multi – If True, then count multiline strings as comment lines as well. 
    This is not always safe because Python multiline strings are not always docstrings.
    """
    variable = metrics.mi_parameters(code_snippet, count_multi=True)

    # Visit the code and compute the Maintainability Index (MI) from it.
    Maintanability_Index = metrics.mi_visit(code_snippet, "multi")

    complexity_measures = dict(
        logical_loc=results[1],
        Halstead_Volume=round(variable[0], 2),
        Cyclomatic_complexity=variable[1],
        percent_lines_of_comment=round(variable[3], 2),
        Maintanability_Index=round(Maintanability_Index, 2),
    )

    return complexity_measures