planner_prompt_str1 = """
Create a data pipeline to accomplish a given task: {task}. Please create a detailed execution plan using only the tools listed below while adhering to the specified constraints.

You have access to only following tools:
====
{tools}
====

The plan should satisfy these constraints:
=====
{context}
=====


Here's an example of the kind of detailed pipeline plan I'm looking for:
=====
{example_task}
=====


The previously generated plan:
=====
{previous_plan}
=====

The Review of the previously generated plan:
=====
{feedback}
=====

update the plan based on the review.
** Each step MUST be as a separate line that includes only a json dictionary without addition description and without indices.
** Show ONLY the one final plan without any additional text or thoughts. Don't include previous plans in the output.
** Make sure the the json are correct and can be parsed without errors.

The final plan:
"""

planner_prompt_str = """
You are an expert in planning data access. For the given context, create a data pipeline to accomplish a given task: {task}
This plan should involve individual tasks that, if executed correctly, will yield the correct answer. 
Do not add any superfluous steps. The result of the final step should be the final answer. 
Make sure that each step has all the information needed - do not skip steps
For each plan, indicate \
which external tool together with the tool input to retrieve evidence. You can store the evidence into a \
variable #E that can be called by later tools. (Plan, #E1, Plan, #E2, Plan, ...). 
Your task is to generate a plan using ONLY the provided tools. Do not use any other tools or methods. 
If you cannot find a suitable tool, use 'tool_not_implemented'
Each step should use only one tool. 
Ensure to specify all required input parameters of the tools.
Ensure that the input parameter of the tools are not hardcoded.
Each step should be a separate line that includes only a JSON dictionary without any additional descriptions.  
Do not provide ANY plan explanations or reviews

You have access to only the following JSON list of tools: {tools}

Context is {context}
~~~~~~
Here's an example of the kind of detailed pipeline plan I'm looking for:
{example_task} 
~~~~~~
The previously generated plan: {previous_plan}
~~~~~~
The Review of the previously generated plan: {feedback} 
"""


# In a separate line, specify user-provided input parameters that will be provided by a user before the execution of the plan. 
# Keep the answer concise; do not print the #E variables separately.
