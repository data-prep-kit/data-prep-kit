judge_prompt_str_dpk = """
Please evaluate the following task and its implementation plan:

Task: {task}
tools:
{tools}
constraints:
{context}
Plan:
{plan}

Please analyze this plan using the following criteria:
    - Does the plan properly addressing the task requirements according to the given tools?
    - Does the plan satisfies all constraints?
    - Does the plan include unnecessary steps (according to the task description and the constraints)?

Please provide:
1. An overall assessment of the plan's validity
2. Specific issues found with constraints (if any), no more than three sentences.
3. Show the unnecessary transforms.

On a different line write either "NEEDS_REVISION: Yes" or "NEEDS_REVISION: No".
"""
  # 4. If the plan is not according to the provided example, for example, it contains reviews or additional comments, please recommend what should be changed. 
  # 3. Wrong use of outputs of the previous steps.

judge_prompt_str1 = """
Please evaluate the following task and its implementation plan:

Task: {task}
~~~~~~
Plan: {plan}
~~~~~~
Tools:  {tools}
~~~~~~
Context: {context}
~~~~~~

Please analyze this plan using the following criteria:
  - Does the plan properly address the task requirements according to the given tools?
  - Does the plan include unnecessary steps?
  - Does the plan satisfies all constraints?
  - Does the plan use tool_not_implemented?
  - Check that the tools' inputs are user-provided inputs or outputs from previous steps.
    
Please provide instructions (no more than three sentences) to the planner to update the plan (if needed) according to the following:
  1. An overall assessment of the plan's validity.
  2. Specific issues found (if any) according to the provided citeria (be specific with no more than three sentences).
  3. Show the values of the input parameters of the tools that are hardcoded values (different than user_input or #E). Please ask the planner to change the hardcoded values to user_input value. Refer just to values of input params.
  4. Show the extra steps.
 
On a different line write either "NEEDS_REVISION: Yes" or "NEEDS_REVISION: No".
"""
