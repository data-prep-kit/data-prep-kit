# Comment cleanser
Please see the set of
[transform project conventions](../../../README.md#transform-project-conventions)
for details on general project conventions, transform configuration,
testing and IDE set up.

## Contributors

- Yash Kalathiya (yashkalathiya164@gmail.com)

## Desciption

This module is designed to detect and remove commented-out code from source files. It leverages the [comment_parser](https://pypi.org/project/comment-parser/) library to accurately extract comments from various programming languages.

### Approach
To distinguish between regular comments (descriptive text) and commented-out code, the module utilizes a Multinomial Naïve Bayes classifier, which classifies comments as follows:

0 → Regular comment (textual description).
1 → Commented-out code (to be removed).
Additionally, the module logs the line numbers where commented-out code is detected using the line_number method from [comment_parser](https://pypi.org/project/comment-parser/).

### Model Details
The classifier uses a [TfidfVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html) with:

- n-grams: (3,4)
- Analyzer: 'char'
This vectorization technique reduces the weight of specific words, allowing the model to focus on a more general context.

#### Training Data
The [model](../model/clf_tfid_char.joblib) was trained on 1.2 million tokens, comprising:

- 300,000 code tokens
- 900,000 text tokens
The dataset was collected from various open-source GitHub repositories, with comments extracted from real-world code. A significant portion of the dataset was sourced from [sourceClassifier](https://github.com/chrislo/sourceclassifier/tree/master/sources) and also [data-prep-kit](https://github.com/data-prep-kit/data-prep-kit).

Functionality
Extract Comments → Uses [comment_parser](https://pypi.org/project/comment-parser/) to fetch all comment lines.
Predict Comment Type → Applies the Naïve Bayes model to classify comments as text or code.
Remove Commented Code → Deletes lines predicted as commented-out code.

## Configuration and command line Options

The set of dictionary keys holding configuration for values are as follows:

* contents_column_name - used to define input column name. Default value is 'contents'.

## Running
You can run the [comment_cleanser_local.py](src/comment_cleanser_local.py) to transform the `test.parquet` file in [test input data](test-data/input) to an `output` directory.  The directory will contain both the new annotated `test.parquet` file and the `metadata.json` file.

### Launched Command Line Options 
When running the transform with the Ray launcher (i.e. TransformLauncher),
the following command line arguments are available in addition to 
the [launcher](../../../../data-processing-lib/doc/launcher-options.md).
* --comment_cleanser_contents_column_name - set the contents_column_name configuration key.
* --comment_cleanser_document_id_column_name - set the document_id_column_name configuration key. 
* --comment_cleanser_n_processes - set the n_processes configuration key. 
* --comment_cleanser_tmp_dir - set the tmp_dir configuration key. 
* --comment_cleanser_timeout - set the timeout configuration key. 
* --comment_cleanser_skip_timeout - set the skip_timeout configuration key. 

## Input and Output

### Input
- **File Format**: Parquet file containing code.
- **Input Column**: The code should be in a column named `content`.
- **Sample Input**:  
  [Sample Input File](./test-data/input/test.parquet)

### Output
- **File Format**: Parquet file with the updated code in the same column.
- **Sample Output**:  
  [Sample Output File](./test-data/expected/test.parquet)

### CLI Syntax
When invoking the CLI, use the following syntax for these parameters:
```
--comment_cleanser_<parameter_name>
```
For example:
```
--comment_cleanser_content_column_name='content'
```

## Example

### Sample Input Code:
```java
// import java.util.Arrays;
import java.util.Arrays;

public class commented_code {
    // Function to calculate the factorial of a number using recursion
    static int factorial(int n) {
        /* Computes factorial of a given number.
           Example:
           factorial(5) => 120
        */
        if (n == 0) return 1;
        return n * factorial(n - 1);
    }

    // TODO: Improve performance of this function (currently inefficient)
    static void slowFunction() {
        // Runs an unnecessary loop with no significant operation.
        for (int i = 0; i < 10000; i++);
    }

    // int addAlternative(int a, int b) {
    //     // Return the computed result.
    //     return result;
    // }

    // int fibonacci(int n) {
    //     if (n <= 1) return n;
    //     return fibonacci(n - 1) + fibonacci(n - 2);
    // }

    // Variable declared but never used (can be removed)
    // int unusedVariable = 42;

    // Debugging statement (no longer needed in production)
    // System.out.println("Debug: Checking function execution");

    // int authenticateUser(String username, String password) {
    //     // Old authentication method, replaced with secure hashing
    //     return username.equals("admin") && password.equals("password");
    // }

    // Old sorting function (Replaced with Arrays.sort())
    // void oldSort(int[] arr) {
    //     // Deprecated: Using Arrays.sort() instead for efficiency
    //     Arrays.sort(arr);
    // }

    // ============================
    //  Edge Cases and Valid Code
    // ============================

    // Function to add two numbers
    static int add(int a, int b) {
        /*
        Adds two integers and returns the result.

        Example:
        add(3, 4) => 7
        */
        return a + b;
    }

    // Multi-line comment: Legacy configuration values
    /*
    Legacy settings (no longer in use)
    String configValue = "old_value";
    String apiKey = "123456789";
    */

    public static void main(String[] args) {
        // Compute factorial of 5 and store the result
        int result = factorial(5);
        System.out.println("Factorial of 5: " + result);
    }
}
```

### Sample Output (with default parameters):
```java
import java.util.Arrays;

public class commented_code {
    // Function to calculate the factorial of a number using recursion
    static int factorial(int n) {
        /* Computes factorial of a given number.
           Example:
           factorial(5) => 120
        */
        if (n == 0) return 1;
        return n * factorial(n - 1);
    }

    // TODO: Improve performance of this function (currently inefficient)
    static void slowFunction() {
        // Runs an unnecessary loop with no significant operation.
        for (int i = 0; i < 10000; i++);
    }

    //     // Return the computed result.


    // Variable declared but never used (can be removed)

    // Debugging statement (no longer needed in production)

    //     // Old authentication method, replaced with secure hashing


    // ============================
    //  Edge Cases and Valid Code
    // ============================

    // Function to add two numbers
    static int add(int a, int b) {
        /*
        Adds two integers and returns the result.

        Example:
        add(3, 4) => 7
        */
        return a + b;
    }

    // Multi-line comment: Legacy configuration values
    Legacy settings (no longer in use)
    String configValue = "old_value";
    String apiKey = "123456789";
    */

    public static void main(String[] args) {
        // Compute factorial of 5 and store the result
        int result = factorial(5);
        System.out.println("Factorial of 5: " + result);
    }
}
```

## Sample Notebook

Check out the [example notebook](../comment_cleanser.ipynb) for further details.


### Transforming data using the transform image

To use the transform image to transform your data, please refer to the 
[running images quickstart](../../../../doc/quick-start/run-transform-image.md),
substituting the name of this transform image and runtime as appropriate.