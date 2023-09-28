# TagTemplatesYaml

## Introduction

Take a step beyond static text and venture into a world where YAML templates are dynamic, interactive landscapes. **TagTemplatesYaml** equips you with a toolkit to bring your templates to life.

## Core Features 🌟

### 1️⃣ Tag Management 🏷️

Seamlessly add and remove tags to populate your templates dynamically.

```python
# Add a new tag
template_manager.createTag("greeting", "Hello, World!")
# Remove a tag
template_manager.removeTag("greeting")
```

### 2️⃣ Dynamic Content Generation ⏳

Infuse real-time data into your templates using tagscript functions.

#### Syntax 🔭

Tagscript expressions are tags within your YAML template. Here's the basic syntax:

```yaml
tags:
  - tag_name: "tagscript: expression"
  - other_tag_name: "tagscript: (param1, param2) => expression"
```

- `tag_name`: This is the name of the tag you want to create.
- `tagscript: expression`: The expression is the Tagscript expression you want to evaluate. It can be any valid Python expression.
- `tagscript: (param1, param2) => expression`: You can also pass parameters to your Tagscript expression. The parameters are passed as a comma-separated list within parentheses.

You can extend the power of TagScript by registering additional modules:

```python
# Initialization
template_manager = TagTemplatesYaml(template_file, tagscript_globals={"datetime": datetime})

# Extending functionalities
template_manager.register_tagscript_globals({"math": math})
```

#### Calling TagScript Functions 🗣️

Use TagScript expressions like any other tag:

```yaml
tags:
  - tag_name: "World!"
  - other_tag_name: 'tagscript: (param) => f"Hello, {param}!"'
template:
  - template_content Hello, <<tag_name>>
  - template_content <<other_tag_name(tag_name)>>
  - template_content <<other_tag_name("Everyone!")>>
```

The output will be:

```yaml
template_content Hello, World!
template_content Hello, World!
template_content Hello, Everyone!
```

⚠️ **Constraints**

1. Tagscript arguments can be other tags, but you can't nest tags that require arguments.
2. Nested TagScripts are not allowed.

#### tagscript Scope 🔭

tagscript functions in tags are constrained to:

- Basic Python functionalities.
- External modules or objects explicitly registered via `tagscript_globals`.

You can register additional modules or objects during TagTemplatesYaml initialization or later using the `register_tagscript_globals` method.

```python
# During Initialization
template_manager = TagTemplatesYaml(template_file, tagscript_globals={"datetime": datetime})

# Later
template_manager.register_tagscript_globals({"math": math})
```

```yaml
# tagscript function to populate a 'date' tag
tags:
  - date: "tagscript: datetime.now().strftime('%Y-%m-%d')"
```

### 3️⃣ Versatility in Template Structure 🎭

TagTemplatesYaml flexes to accommodate both dictionary-based and string-based templates.

```yaml
# Dictionary-based template
template:
  name: <<username>>
  status: <<mood>>

# String-based template
template: "Today's weather is <<weather>> and the time is <<time>>."
```

### 4️⃣ Exception Handling with Precision 🚨

Exception handling is meticulously crafted through a lineup of custom exception classes, each designed for a specific type of debugging and error resolution:

- **TemplateVersionError**: Focuses on issues related to incompatible template versions, aiding in the identification of versioning conflicts.
- **TemplateInvalidError**: Designed to catch syntactical or logical issues in the template, streamlining the debugging process for malformed templates.
- **TemplateFileError**: Addresses file-related complications, such as difficulties in reading a template file.
- **TagScriptSyntaxError**: Targets errors within the syntax of a TagScript expression, making it easier to debug TagScript-related issues.
- **TagScriptRuntimeError**: Catches errors that occur during the runtime evaluation of a TagScript expression.
- **TagScriptArgumentError**: Deals with incorrect or malformed arguments passed to a TagScript expression.
- **TagScriptSandboxError**: Captures violations of sandboxed environment constraints in TagScript, ensuring that all TagScript expressions adhere to preset limitations.

Each of these bolded custom exception classes fine-tunes the debugging and error resolution process, allowing for a highly focused and efficient troubleshooting experience.

## Quality Assurance: Test-Driven Approach 🛠️

A comprehensive test suite assures that TagTemplatesYaml operates reliably, covering everything from basic tag management to intricate error-handling scenarios.