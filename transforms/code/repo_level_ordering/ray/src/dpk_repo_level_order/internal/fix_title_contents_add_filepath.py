import pandas as pd


def fix_title_contents(title_column_name='title',
                       repo_column_name='repo_name',
                       dataset_column_name='dataset',
                       contents_column_name='contents'):

    def fix_title_contents_func(table):
        table = fix_title(table, title_column_name, repo_column_name, dataset_column_name)
        table = fix_contents(table, contents_column_name, dataset_column_name)
        return table

    return fix_title_contents_func


def fix_bluepile_github_title(title: str, repo_name: str):
    # Example - Filepath - dive-in-mall-master/mall-mini-program/components/hot-list/index.js, Repo Name - liuhuiAndroid/dive-in-mall
    actual_repo_name = repo_name.split("/")[-1].strip("/")
    if title.startswith(actual_repo_name):
        title = '/'.join(title.split("/")[1:])
    return title

def fix_abap_title(title: str, repo_name: str):
    if title.startswith(repo_name):
        title = title[len(repo_name)+1:]
    return title

def fix_title(table: pd.DataFrame, title_column_name: str, repo_column_name: str, dataset_column_name: str):
    # Remove forward slash from start of file - also removes forard slash of abap dataset
    table[title_column_name] = table[title_column_name].str.lstrip("/")
    # Remove repo name, org name and branch name from title
    bg_idx = (table[dataset_column_name] == "bluepile_github")
    if bg_idx.any():
        table.loc[bg_idx, title_column_name] = table.loc[bg_idx].apply(
            lambda row: fix_bluepile_github_title(row[title_column_name], row[repo_column_name]), axis=1)
    abap_idx = (table[dataset_column_name] == "abap")
    if abap_idx.any():
        table.loc[abap_idx, title_column_name] = table.loc[abap_idx].apply(
            lambda row: fix_abap_title(row[title_column_name], row[repo_column_name]), axis=1)
    return table

def fix_startcoder_contents(contents: str):
    def is_tag_absent(line: str):
        if line.startswith("<filename>"):
            return False
        if line.startswith("<reponame>"):
            return False
        if line.startswith("<gh_stars>"):
            return False
        return True

    contents_lines = contents.splitlines()
    contents_lines = [ele for ele in contents_lines if is_tag_absent(ele)]
    return '\n'.join(contents_lines)

def fix_contents(table, contents_column_name, dataset_column_name):
    sc_idx = (table[dataset_column_name] == "starcoder")
    if sc_idx.any():
        table.loc[sc_idx, contents_column_name] = table.loc[sc_idx, contents_column_name].apply(fix_startcoder_contents)
    return table

def prepend_filename_token_filepath(title, repo, contents):
    file_path = f"{repo.split('/')[-1]}/{title}"
    result = f"<filename>{file_path}\n{contents}"
    return result

if __name__ == "__main__":
    df = pd.read_csv("/data/shanmukh/forked_repos/data-prep-kit/sc.csv")
    df_copy = df.copy(deep=True)
    df = fix_title_contents(title_column_name="filepath")(df)
    df
