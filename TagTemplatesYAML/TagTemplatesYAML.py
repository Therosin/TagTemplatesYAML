import logging
import re
from os import path
import yaml

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

# Version of the TagTemplatesYaml package
template_manager_version = "1.0"

"""
    TagScript is a simple scripting language that allows for dynamic tags in templates.
    for all intents and purposes, its a wrapper around lambda functions with a modified syntax to support serializing and deserializing.
    security is handled via simple sandboxing, with a mutable environment.

    TagScript syntax:
        - basic syntax with no arguments:
            `tagscript: code`
            eg: `tagscript: 1 + 1` - returns > 2
        - syntax with arguments:
            `tagscript: (args...) => code`
            eg: `tagscript: (a, b) => a + b` - called with `(1, 1)` returns > 2
"""

safe_builtins = dict(__builtins__)
del safe_builtins["eval"]
del safe_builtins["exec"]
del safe_builtins["open"]
# remove all the unsafe builtins

unsafe_modules = [
    "os",
    "sys",
    "subprocess",
    "shutil",
    "importlib",
    "importlib.*",
]


def safe_import(name, *args, **kwargs):
    if name in unsafe_modules:
        raise ImportError(f"Importing {name} is not allowed")
    return __import__(name, *args, **kwargs)


safe_builtins["__import__"] = safe_import


class InvalidTagScriptError(Exception):
    """
    Base class for all TagScript errors.
    """

    pass


class TagScriptSyntaxError(InvalidTagScriptError):
    """
    Raised when a syntax error is encountered in a TagScript.
    """

    pass


class TagScriptRuntimeError(InvalidTagScriptError):
    """
    Raised when a runtime error is encountered in a TagScript.
    """

    pass


class TagScriptArgumentError(InvalidTagScriptError):
    """
    Raised when a TagScript is called with invalid arguments.
    """

    pass


class TagScriptSandboxError(InvalidTagScriptError):
    """
    Raised when a sandbox error is encountered in a TagScript.
    """

    pass


# regex to detect tagscript syntax
# this will match tagscript: code and tagscript: (args...) => code
tagscript_param_regex = re.compile(r"tagscript: \((.*)\)\s*=>\s*(.*)|tagscript: (.*)")


def parseTagScript(code):
    """
    Parse a TagScript.
    Returns a tuple of (is_tagscript, code, args)
    is_tagscript: bool - whether or not the code is a tagscript
    code: str - the code to run
    args: list - the arguments to pass to the code
    """
    found = re.match(tagscript_param_regex, code)
    if found:
        groups = found.groups()
        if groups[2] is not None:
            # tagscript: code
            parsed_code = groups[2]
            logger.debug(f"TagScript parsed without Args: {code} -> {parsed_code}")
            return True, parsed_code, []
        elif groups[0] is not None and groups[1] is not None:
            # tagscript: (args...) => code
            parsed_args, parsed_code = groups[0], groups[1]
            logger.debug(
                f"TagScript parsed with Args: {code} -> ({parsed_args}) {parsed_code}"
            )
            return True, parsed_code, [arg.strip() for arg in parsed_args.split(",")]

        # if we get here, it's not a tagscript
        return False, None, None


# TagScript class
class TagScript:
    def __init__(self, name="default", env={}):
        """
        Create a new TagScript object.
        env: dict - the environment to use for the TagScript
        """
        self.name = name
        tagscript_env = {
            "__builtins__": safe_builtins.copy(),
            "logger": logging.getLogger(f"TagScript.{name}"),
        }
        tagscript_env.update(env)
        self.env = tagscript_env

    def run(self, code, args=[]):
        # try to parse the code
        is_tagscript, parsed_code, parsed_args = parseTagScript(code)
        logger.debug(f"TagScript.{self.name}: {code} -> ({parsed_args}) {parsed_code}")
        if not is_tagscript:
            raise InvalidTagScriptError(
                f"Invalid TagScript: {code} in TagScript.{self.name}"
            )
        else:
            try:
                if parsed_args:
                    logger.debug(
                        f"TagScript.{self.name}: {parsed_args} -> ({args}) {parsed_code}"
                    )
                    # Create a lambda function with the given code and args
                    lambda_func = eval(
                        f"lambda {', '.join(parsed_args)}: {parsed_code}", self.env
                    )
                    return lambda_func(*args)
                else:
                    logger.debug(f"TagScript.{self.name}: {parsed_code}")
                    # No arguments, just evaluate the code
                    return eval(parsed_code, self.env)
            except Exception as e:
                raise TagScriptRuntimeError(
                    f"Error running TagScript: {code} in TagScript.{self.name}"
                ) from e

    def register_globals(self, globals):
        """
        Register multiple global variables in the TagScript environment.
        globals: dict - the globals to register
        """
        self.env.update(globals)

    def unregister_globals(self, globals):
        """
        Unregister multiple global variables in the TagScript environment.
        globals: dict - the globals to unregister
        """
        for key in globals:
            if key in self.env:
                del self.env[key]


class TemplateVersionError(Exception):
    pass


class TemplateInvalidError(Exception):
    pass


class TemplateFileError(Exception):
    pass


class TagTemplateYAML:
    """
    Manages Templated YAML files, featuring placeholders that can be replaced with values or tagscript functions.
    Warning: tagscript functions allow for unsafe code execution. Use with caution.
    """

    def __init__(self, template_file=None, tagscript_globals=None):
        """
        Initialize the TagTemplatesYaml object.
        Parameters:
            template_file (str, optional): The path to the template YAML file.
            tagscript_globals (dict, optional): A dictionary of global variables that will be available to the tagscript functions.
        """
        self.tags = {}
        self.template_file = None
        self.template_content = None

        if template_file:
            if path.exists(template_file) and template_file.endswith(".yaml"):
                logger.debug(
                    f"Initializing TagTemplatesYaml with template file: {template_file}"
                )
                self.template_file = template_file
            else:
                raise TemplateFileError(
                    f"Template file: {template_file} does not exist or is not a YAML file."
                )

        # use the template file as the name
        if self.template_file:
            self.name = f"TagTemplatesYaml: {path.basename(self.template_file)}"
        else:
            self.name = "TagTemplatesYaml: default"

        if tagscript_globals:
            logger.debug(
                f"Initializing {self.name} with tagscript globals: {', '.join(tagscript_globals.keys())}"
            )
            self.tagscript_globals = tagscript_globals
        else:
            self.tagscript_globals = {}

        self.TemplateEngine = TagScript(self.name, self.tagscript_globals)

        if self.template_file:
            self.loadTemplate()

        logger.debug(
            f"Initialized {self.name} from template file: {self.template_file} \ncontaining tags: {', '.join(self.tags.keys())} \ntagscript globals: {', '.join(self.tagscript_globals.keys())}"
        )

    def loadTemplate(self, template_file=None):
        """
        Load the template from a YAML file.
        """
        if template_file:
            self.template_file = template_file
        if not self.template_file:
            raise TemplateFileError("No template file specified.")

        with open(self.template_file, "r") as file:
            raw_content = file.read()

        parsed_content = yaml.safe_load(raw_content)
        # there must be a version key in the template, and it must match the current version
        if (
            "version" not in parsed_content
            or parsed_content["version"] != template_manager_version
        ):
            raise TemplateVersionError(
                f"Invalid template version: {parsed_content.get('version')}, expected: {template_manager_version}"
            )

        # tags is optional
        if "tags" in parsed_content:
            logger.debug("Loading tags from template")
            for tag_def in parsed_content["tags"]:
                for tag_name, value_or_tagscript_str in tag_def.items():
                    self.createTag(tag_name, value_or_tagscript_str)

        # template is required
        if "template" not in parsed_content:
            raise TemplateInvalidError("Template must contain a 'template' key.")
        self.template_content = parsed_content.get("template")
        logger.debug(f"Loaded template from file: {self.template_file}")
        return parsed_content

    def saveTemplate(self, template_file=None):
        """
        Save the current state of the template and tags to a YAML file.
        """
        if template_file:
            self.template_file = template_file
        if not self.template_file:
            raise TemplateFileError("No template file specified.")

        template_dict = {"version": template_manager_version}
        if len(self.tags) > 0:
            logger.debug("Saving tags to template")
            template_dict["tags"] = [{k: v} for k, v in self.tags.items()]

        template_dict["template"] = self.template_content

        yaml_content = yaml.dump(template_dict)

        with open(self.template_file, "w") as file:
            try:
                file.write(yaml_content)
            except Exception as exc:
                raise TemplateFileError(f"Error writing template file: {exc}")
        logger.debug(f"Saved template to file: {self.template_file}")

    def createTag(self, tag_name, value_or_tagscript):
        """
        Register a new tag (placeholder) with a set value or tagscript function.
        """
        if tag_name in self.tags:
            logger.warning(f"Replacing existing tag: {tag_name}")
        self.tags[tag_name] = value_or_tagscript
        logger.debug(f"Created tag: {tag_name} with value: {value_or_tagscript}")

    def removeTag(self, tag_name):
        """
        Remove a registered tag (placeholder).
        """
        if tag_name in self.tags:
            del self.tags[tag_name]
        else:
            logger.warning(f"Attempted to remove nonexistent tag: {tag_name}")

    def register_tagscript_globals(self, tagscript_globals):
        """
        Register a dictionary of global variables that will be available to the tagscript functions.
        """
        for key, value in tagscript_globals.items():
            if key in self.tagscript_globals:
                logger.warning(
                    f"Attempted to register duplicate tagscript global: {key} - ignoring"
                )
            else:
                logger.debug(f"Registering tagscript global: {key}")
                self.tagscript_globals[key] = value
                self.TemplateEngine.register_globals({key: value})

    def unregister_tagscript_globals(self, tagscript_globals):
        """
        Unregister list of global variables that will be available to the tagscript functions.
        """
        for key in tagscript_globals:
            if key in self.tagscript_globals:
                logger.debug(f"Unregistering tagscript global: {key}")
                del self.tagscript_globals[key]
                self.TemplateEngine.unregister_globals([key])
            else:
                logger.warning(
                    f"Attempted to unregister nonexistent tagscript global: {key} - ignoring"
                )

    def replacePlaceholders(self, content):
        """
        Replace the placeholders in the given content based on the registered tags and tagscripts.
        """

        # Function to evaluate a single tag
        def evaluate_tag(tag):
            if tag in self.tags:
                if self.tags[tag].startswith("tagscript:"):
                    script = self.tags[tag]
                    logger.debug(f"Evaluating argument tagscript: {script}")
                    return self.TemplateEngine.run(script, [])
                else:
                    return self.tags[tag]
            return None

        # Regex patterns
        simple_tag_pattern = re.compile(r"<<([^>(]+)>>")
        param_tag_pattern = re.compile(r"<<([^>]+)\(([^>]+)\)>>")

        # Replace simple tags using evaluate_tag function
        for match in simple_tag_pattern.findall(content):
            value = evaluate_tag(match)  # Evaluate the argument as a tag
            if value is not None:
                content = content.replace(f"<<{match}>>", str(value))

        # Replace tags with parameters
        for match, args in param_tag_pattern.findall(content):
            if match in self.tags and self.tags[match].startswith("tagscript:"):
                script = self.tags[match]
                params = []
                for arg in args.split(","):
                    arg = arg.strip()
                    value = evaluate_tag(arg)  # Evaluate the argument as a tag
                    if value is None:
                        value = arg  # Use the argument as-is if it's not a tag
                    params.append(value)
                value = self.TemplateEngine.run(script, params)
                content = content.replace(f"<<{match}({args})>>", str(value))
        return content

    def parseTemplate(self):
        """
        Parse the loaded template, evaluating any tagscript expressions and replacing placeholders.
        Returns:
            The parsed content of the template.
        """
        if isinstance(self.template_content, str):
            logger.debug("parseTemplate: template is a string")
            return self.replacePlaceholders(self.template_content)
        elif isinstance(self.template_content, dict):
            logger.debug("parseTemplate: template is a dictionary")
            parsed_content = self.template_content.copy()
            for key, value in parsed_content.items():
                parsed_content[key] = self.replacePlaceholders(str(value))
            return parsed_content
        else:
            raise TemplateInvalidError("Invalid template content.")
