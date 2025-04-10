# Header cleanser
Please see the set of
[transform project conventions](../../../README.md#transform-project-conventions)
for details on general project conventions, transform configuration,
testing and IDE set up.

## Contributors

- Yash Kalathiya (yashkalathiya164@gmail.com)

## Desciption

The **Header Cleanser** module is a versatile tool designed to remove license and copyright headers from code files. It supports over 90 programming languages and utilizes the [ScanCode Toolkit](https://scancode-toolkit.readthedocs.io/en/stable/getting-started/install.html) to identify license and copyright information within the codebase.

## Configuration and command line Options

The set of dictionary keys holding configuration for values are as follows:

* contents_column_name - used to define input column name. Default value is 'contents'.
* license - write 'true' to remove license from input data else 'false'. By default set as 'true'.
* copyright - write 'true' to remove copyright from input data else 'false'. by default set as 'true'.

## Running
You can run the [header_cleanser_local.py](src/header_cleanser_local.py) (python-only implementation) or [header_cleanser_local_ray.py](../ray/src/header_cleanser_local_ray.py) (ray-based  implementation) to transform the `test1.parquet` file in [test input data](test-data/input) to an `output` directory.  The directory will contain both the new annotated `test1.parquet` file and the `metadata.json` file.

## Running

### Launched Command Line Options 
When running the transform with the Ray launcher (i.e. TransformLauncher),
the following command line arguments are available in addition to 
the [launcher](../../../../data-processing-lib/doc/launcher-options.md).
* --header_cleanser_contents_column_name - set the contents_column_name configuration key.
* --header_cleanser_document_id_column_name - set the document_id_column_name configuration key.
* --header_cleanser_license - set the license configuration key.
* --header_cleanser_copyright - set the copyright configuration key. 
* --header_cleanser_n_processes - set the n_processes configuration key. 
* --header_cleanser_tmp_dir - set the tmp_dir configuration key. 
* --header_cleanser_timeout - set the timeout configuration key. 
* --header_cleanser_skip_timeout - set the skip_timeout configuration key. 

## Input and Output

### Input
- **File Format**: Parquet file containing code.
- **Input Column**: The code should be in a column named `content`.
- **Sample Input**:  
  [Sample Input File](./test-data/input/test1.parquet)

### Output
- **File Format**: Parquet file with the updated code in the same column.
- **Sample Output**:  
  [Sample Output File](./test-data/expected/license-and-copyright-local/test1.parquet)

### CLI Syntax
When invoking the CLI, use the following syntax for these parameters:
```
--header_cleanser_<parameter_name>
```
For example:
```
--header_cleanser_content_column_name='content'
```

## Example

### Sample Input Code:
```java
/*
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.jstevenperry.intro;

import java.util.logging.Logger;

// This is the main public class representing a Person
public class Person {
    private static final Logger logger = Logger.getLogger(Person.class.getName());

    private String name;
    private int age;
    private int height;
    private int weight;
    private String eyeColor;
    private String gender;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public int getAge() {
        return age;
    }

    public void setAge(int age) {
        this.age = age;
    }

    public int getHeight() {
        return height;
    }

    public void setHeight(int height) {
        this.height = height;
    }

    public int getWeight() {
        return weight;
    }

    public void setWeight(int weight) {
        this.weight = weight;
    }

    public String getEyeColor() {
        return eyeColor;
    }

    public void setEyeColor(String eyeColor) {
        this.eyeColor = eyeColor;
    }

    public String getGender() {
        return gender;
    }

    public void setGender(String gender) {
        this.gender = gender;
    }

    public Person(String name, int age, int height, int weight, String eyeColor, String gender) {
        super();
        this.name = name;
        this.age = age;
        this.height = height;
        this.weight = weight;
        this.eyeColor = eyeColor;
        this.gender = gender;

        logger.info("Created Person object with name '" + getName() + "'");
    }
}
```

### Sample Output (with default parameters):
```java
package com.jstevenperry.intro;

import java.util.logging.Logger;

/// This is the main public class representing a Person
public class Person {

    private static final Logger logger = Logger.getLogger(Person.class.getName());

    private String name;
    private int age;
    private int height;
    private int weight;
    private String eyeColor;
    private String gender;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public int getAge() {
        return age;
    }

    public void setAge(int age) {
        this.age = age;
    }

    public int getHeight() {
        return height;
    }

    public void setHeight(int height) {
        this.height = height;
    }

    public int getWeight() {
        return weight;
    }

    public void setWeight(int weight) {
        this.weight = weight;
    }

    public String getEyeColor() {
        return eyeColor;
    }

    public void setEyeColor(String eyeColor) {
        this.eyeColor = eyeColor;
    }

    public String getGender() {
        return gender;
    }

    public void setGender(String gender) {
        this.gender = gender;
    }

    public Person(String name, int age, int height, int weight, String eyeColor, String gender) {
        super();
        this.name = name;
        this.age = age;
        this.height = height;
        this.weight = weight;
        this.eyeColor = eyeColor;
        this.gender = gender;

        logger.info("Created Person object with name '" + getName() + "'");
    }
}
```

## Sample Notebook

Check out the [example notebook](../header_cleanser.ipynb) for further details.


### Transforming data using the transform image

To use the transform image to transform your data, please refer to the 
[running images quickstart](../../../../doc/quick-start/run-transform-image.md),
substituting the name of this transform image and runtime as appropriate.