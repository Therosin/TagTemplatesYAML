import pytest
import yaml
import os
from TagTemplatesYAML import (
    TagTemplateYAML,
    TemplateFileError,
    TemplateVersionError,
    TemplateInvalidError,
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Define global TemplateContent with a 'tags' section
TemplateContent = """
version: "1.0"
name: "test_template"
tags:
  - new_placeholder: "Some Value"
  - date: "tagscript: datetime.now().strftime('%Y-%m-%d')"
template:
  name: <<user>>
  realm: <<context>>
  player: <<char>>
"""


@pytest.fixture(scope="module")
def setup_template_manager():
    template_file = "./test_template.yaml"
    # Create a test template file
    with open(template_file, "w") as file:
        file.write(TemplateContent)

    # Create the template manager
    template_manager = TagTemplateYAML(
        template_file, tagscript_globals={"datetime": datetime}
    )
    # Create some tags
    template_manager.createTag("user", "John Doe")
    template_manager.createTag("context", "Digital Exploration")
    template_manager.createTag("char", "A")
    yield template_manager

    # Cleanup: remove the test template file
    os.remove(template_file)


def test_create_tag(setup_template_manager):
    template_manager = setup_template_manager
    template_manager.createTag("new_tag", "New Value")
    # template_manager.tags should now contain the new tag
    assert "new_tag" in template_manager.tags
    # The value of the new tag should be "New Value"
    assert template_manager.tags["new_tag"] == "New Value"


def test_remove_tag(setup_template_manager):
    template_manager = setup_template_manager
    template_manager.removeTag("new_tag")
    # template_manager.tags should no longer contain the new tag
    assert "new_tag" not in template_manager.tags


def test_replace_placeholders(setup_template_manager):
    template_manager = setup_template_manager
    # The 'new_placeholder' should have been loaded from the YAML and should return "Some Value"
    assert template_manager.replacePlaceholders("<<new_placeholder>>") == "Some Value"


def test_replace_multiple_placeholders(setup_template_manager):
    template_manager = setup_template_manager
    raw_content = "name: <<user>>\nrealm: <<context>>\nplayer: <<char>>"
    processed_content = template_manager.replacePlaceholders(raw_content)
    # fake load the YAML
    parsed_content = yaml.safe_load(processed_content)
    expected_content = {
        "name": "John Doe",
        "realm": "Digital Exploration",
        "player": "A",
    }
    assert parsed_content == expected_content


def test_tagscript_tags(setup_template_manager):
    template_manager = setup_template_manager
    # Create a tag with a tagscript function returning the current date
    template_manager.createTag("date", "tagscript: datetime.now().strftime('%Y-%m-%d')")
    # Create a tag with a tagscript function returning the current epoch time
    template_manager.createTag("timestamp", "tagscript: datetime.now().timestamp()")
    # Replace the placeholder with the dynamic tag
    dynamic_date = template_manager.replacePlaceholders("<<date>>")
    # Try to determine if the date is valid
    datetime.strptime(dynamic_date, "%Y-%m-%d")
    # Replace the placeholder with the dynamic tag
    dynamic_timestamp = template_manager.replacePlaceholders("<<timestamp>>")
    # Try to determine if the timestamp is valid
    assert isinstance(dynamic_timestamp, str)
    assert isinstance(float(dynamic_timestamp), float)


def test_tagscript_tag_params(setup_template_manager):
    template_manager = setup_template_manager
    # Create a tag with a tagscript function returning the current date
    template_manager.createTag("params", "hello")
    template_manager.createTag("print", 'tagscript: (args) => f"{args}"')
    # Replace the placeholder with the dynamic tag
    result = template_manager.replacePlaceholders("<<print(params)>>")
    logger.debug(f"Result: {result}")


string_template_content = """
version: "1.0"
name: "test_string_template"
template: |
    Hello <<name>>!
    Today is <<date>>.
    The current timestamp is <<timestamp>>.
"""


def test_string_template():
    # write the template to a file
    template_file = "./test_string_template.yaml"
    with open(template_file, "w") as file:
        file.write(string_template_content)
    # create the template manager
    template_manager = TagTemplateYAML(template_file)
    template_manager.register_tagscript_globals({"datetime": datetime})
    # Create <<name>> tag
    template_manager.createTag("name", "John Doe")
    # Create a tag with a tagscript function returning the current date
    template_manager.createTag("date", "tagscript: datetime.now().strftime('%Y-%m-%d')")
    # Create a tag with a tagscript function returning the current epoch time (fake timestamp)
    the_time = datetime.now().timestamp()
    template_manager.createTag("timestamp", f"tagscript: {the_time}")
    # Replace the placeholder with the dynamic tag
    parsed_template = template_manager.parseTemplate()
    assert isinstance(parsed_template, str)
    assert "Hello John Doe!" in parsed_template
    assert f"Today is {datetime.now().strftime('%Y-%m-%d')}." in parsed_template
    assert f"The current timestamp is {the_time}." in parsed_template
    # Cleanup: remove the test template file
    os.remove(template_file)


template_file = "./test_save-load_template.yaml"


def test_load_template():
    # write the template to a file
    with open(template_file, "w") as file:
        file.write(TemplateContent)
    # create the template manager
    template_manager = TagTemplateYAML(
        template_file, tagscript_globals={"datetime": datetime}
    )
    template_manager.createTag("user", "John Doe")
    template_manager.createTag("context", "Digital Exploration")
    template_manager.createTag("char", "A")

    parsed_template = template_manager.parseTemplate()
    assert isinstance(parsed_template, dict)
    assert parsed_template["name"] == "John Doe"
    assert parsed_template["realm"] == "Digital Exploration"
    assert parsed_template["player"] == "A"

    # Cleanup: remove the test template file
    os.remove(template_file)


def test_save_template(setup_template_manager):
    # create the template manager
    template_manager = setup_template_manager
    # save the template to a file
    template_manager.saveTemplate(template_file)

    with open(template_file, "r") as file:
        raw_content = file.read()
    parsed_content = yaml.safe_load(raw_content)
    assert parsed_content["version"] == "1.0"
    tags = parsed_content["tags"]
    assert len(tags) == 10
    assert {"new_placeholder": "Some Value"} in tags
    assert {"date": "tagscript: datetime.now().strftime('%Y-%m-%d')"} in tags
    assert {"user": "John Doe"} in tags
    assert {"context": "Digital Exploration"} in tags
    assert {"char": "A"} in tags
    assert {"timestamp": "tagscript: datetime.now().timestamp()"} in tags
    # Cleanup: remove the test template file
    os.remove(template_file)


template_content_invalid_version = """
version: "2.0"
name: "test_invalid_version"
template: |
    Hello <<name>>!
    Today is <<date>>.
    The current timestamp is <<timestamp>>.
"""


def test_invalid_version():
    # write the template to a file
    template_file = "./test_invalid_version.yaml"
    with open(template_file, "w") as file:
        file.write(template_content_invalid_version)
    # create the template manager
    with pytest.raises(TemplateVersionError):
        template_manager = TagTemplateYAML(
            template_file, tagscript_globals={"datetime": datetime}
        )
    # Cleanup: remove the test template file
    os.remove(template_file)


template_content_missing_template = """
version: "1.0"
name: "test_missing_template"
tags:
    - new_placeholder: "Some Value"
    - date: "tagscript: datetime.now().strftime('%Y-%m-%d')"
"""


def test_missing_template():
    # write the template to a file
    template_file = "./test_missing_template.yaml"
    with open(template_file, "w") as file:
        file.write(template_content_missing_template)
    # create the template manager
    with pytest.raises(TemplateInvalidError):
        template_manager = TagTemplateYAML(
            template_file, tagscript_globals={"datetime": datetime}
        )
    # Cleanup: remove the test template file
    os.remove(template_file)


def test_invalid_file():
    # create the template manager
    with pytest.raises(TemplateFileError):
        template_manager = TagTemplateYAML(
            "invalid_file.yaml", tagscript_globals={"datetime": datetime}
        )
