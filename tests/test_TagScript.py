from TagTemplatesYAML import TagScript, TagScriptSyntaxError, TagScriptRuntimeError, TagScriptArgumentError, TagScriptSandboxError
import pytest
import logging

logger = logging.getLogger(__name__)

@pytest.fixture(scope="module")
def setup_tagscript():
    tagscript = TagScript()
    yield tagscript


class TestTagScriptBasicFunctionality:

    def test_tagscript_basic_syntax(self, setup_tagscript):
        tagscript = setup_tagscript
        # should handle basic arithmetic
        assert tagscript.run("tagscript: 1 + 1") == 2
        # should handle basic string operations
        assert tagscript.run("tagscript: 'a' + 'b'") == "ab"
        # should handle basic boolean operations
        assert tagscript.run("tagscript: True and True") == True
        assert tagscript.run("tagscript: True or False") == True
        # should handle basic list operations
        assert tagscript.run("tagscript: [1, 2, 3]") == [1, 2, 3]
        # should handle basic dict operations
        assert tagscript.run("tagscript: {'a': 1, 'b': 2}") == {"a": 1, "b": 2}
        
    def test_tagscript_basic_syntax_with_args(self, setup_tagscript):
        tagscript = setup_tagscript
        # should handle basic arithmetic
        assert tagscript.run("tagscript: (a, b) => a + b", [1, 1]) == 2
        # should handle basic string operations
        assert tagscript.run("tagscript: (a, b) => a + b", ["a", "b"]) == "ab"
        # should handle basic boolean operations
        assert tagscript.run("tagscript: (a, b) => a and b", [True, True]) == True
        assert tagscript.run("tagscript: (a, b) => a or b", [True, False]) == True
        # should handle basic list operations
        assert tagscript.run("tagscript: (a, b) => a + b", [[1, 2], [3, 4]]) == [1, 2, 3, 4]
        # should handle basic dict operations
        assert tagscript.run("tagscript: (a, b) => {**a, **b}", [{"a": 1}, {"b": 2}]) == {"a": 1, "b": 2}

    def test_tagscript_basic_syntax_with_kwargs(self, setup_tagscript):
        tagscript = setup_tagscript
        # should handle basic arithmetic
        assert tagscript.run("tagscript: (a=1, b=1) => a + b") == 2
        # should handle basic string operations
        assert tagscript.run("tagscript: (a='a', b='b') => a + b") == "ab"
        # should handle basic boolean operations
        assert tagscript.run("tagscript: (a=True, b=True) => a and b") == True
        assert tagscript.run("tagscript: (a=True, b=False) => a or b") == True
        # should handle basic list operations
        assert tagscript.run("tagscript: (a=[1, 2], b=[3, 4]) => a + b") == [1, 2, 3, 4]
        # should handle basic dict operations
        assert tagscript.run("tagscript: (a={'a': 1}, b={'b': 2}) => {**a, **b}") == {"a": 1, "b": 2}

class TestTagScriptWithGlobals:

    def test_tagscript_globals(self, setup_tagscript):
        tagscript = setup_tagscript
        assert tagscript.run("tagscript: logger") == tagscript.env["logger"]

    def test_tagscript_add_globals(self, setup_tagscript):
        tagscript = setup_tagscript
        tagscript.register_globals({"test": "test"})
        assert tagscript.run("tagscript: test") == "test"

    def test_tagscript_remove_globals(self, setup_tagscript):
        tagscript = setup_tagscript
        tagscript.register_globals({"test": "test"})
        assert tagscript.run("tagscript: test") == "test"
        tagscript.unregister_globals(["test"])
        with pytest.raises(TagScriptRuntimeError or NameError):
            tagscript.run("tagscript: test")
