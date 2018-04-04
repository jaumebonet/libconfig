# @Author: Jaume Bonet <bonet>
# @Date:   04-Apr-2018
# @Email:  jaume.bonet@gmail.com
# @Filename: test_libconfig.py
# @Last modified by:   bonet
# @Last modified time: 04-Apr-2018


import os

import pytest

import libconfig as cfg


class TestLibConfig(object):

    def test_register(self):
        """
        Check that register is possible
        """
        cfg.register_option("numeric", "integer_fixed", 4, "int",
                            "this is a fixed integer", locked=True)
        cfg.register_option("numeric", "float_free", 2.3, "float",
                            "this is a free float")
        with pytest.raises(KeyError):
            cfg.register_option("numeric", "integer_fixed", 2, "int",
                                "cannot overwrite a register!")

        cfg.register_option("boolean", "boolean", False, "bool",
                            "this is a simple boolean.")

        cfg.register_option("string", "option_text", "alpha", "text",
                            "this string is limited to some options.",
                            values=["alpha", "beta", "gamma"])
        cfg.register_option("string", "free_text", "omega", "string",
                            "this string can be anything.")

        cfg.register_option("path", "in", os.path.expanduser('~'), "path_in",
                            "this path needs to exist.")
        with pytest.raises(ValueError):
            cfg.register_option("path", "in2", "/no/path/at/all", "path_in",
                                "it will fail if it doesn't.")
        cfg.register_option("path", "out", "/no/path/at/all", "path_out",
                            "this path does not need to exist.")

    def test_locked_and_limited_options(self):
        """
        Test the workings of locked and optional values
        """
        with pytest.raises(ValueError):
            cfg.set_option("numeric", "integer_fixed", 6)

        assert cfg.check_option("string", "option_text", "beta") is True
        assert cfg.check_option("string", "option_text", "epsilon") is False
        cfg.set_option("string", "option_text", "beta")
        with pytest.raises(ValueError):
            cfg.set_option("string", "option_text", "epsilon")
        assert cfg.get_option("string", "option_text") == "beta"
        assert len(cfg.get_option_alternatives("string", "option_text")) == 3

        cfg.set_option("numeric", "float_free", 33.6)
        cfg.lock_option("numeric", "float_free")
        with pytest.raises(ValueError):
            cfg.set_option("numeric", "float_free", 6.2)

    def test_change_type(self):
        """
        Make sure that non-specified types cannot be provided.
        """
        with pytest.raises(ValueError):
            cfg.set_option("boolean", "boolean", "the_truth")

        cfg.set_option("string", "free_text", "epsilon")
        with pytest.raises(ValueError):
            cfg.set_option("string", "free_text", 23.45)
        assert cfg.get_option("string", "free_text") == "epsilon"

        cfg.set_option("path", "in", os.getcwd())
        with pytest.raises(ValueError):
            cfg.set_option("path", "in", "/not/a/real/path")
        assert cfg.get_option("path", "in") == os.getcwd()

    @pytest.fixture(scope='session')
    def test_write(self, tmpdir_factory):
        """
        Evaluate if we can dump the options to a file.
        """
        d = str(tmpdir_factory.mkdir("dumps"))
        cfg.write_options_to_JSON(os.path.join(d, "config.json"))
        cfg.write_options_to_YAML(os.path.join(d, "config.yaml"))

    @pytest.fixture(scope='session')
    def test_read(self, tmpdir_factory):
        """
        See if we can read from option files.
        """
        d = str(tmpdir_factory.mkdir("dumps"))

        cfg.reset_options(empty=False)
        assert cfg.get_option("string", "free_text") == "omega"
        assert cfg.get_option("string", "option_text") == "alpha"
        cfg.set_options_from_JSON(os.path.join(d, "config.json"))
        assert cfg.get_option("path", "in") == os.getcwd()
        assert cfg.get_option("string", "free_text") == "epsilon"
        assert cfg.get_option("string", "option_text") == "beta"

        cfg.reset_options(empty=False)
        assert cfg.get_option("string", "free_text") == "omega"
        assert cfg.get_option("string", "option_text") == "alpha"
        cfg.set_options_from_YAML(os.path.join(d, "config.yaml"))
        assert cfg.get_option("path", "in") == os.getcwd()
        assert cfg.get_option("string", "free_text") == "epsilon"
        assert cfg.get_option("string", "option_text") == "beta"
        assert cfg.get_option("numeric", "integer_fixed") == 6

    def test_resets(self):
        """
        See if we can get back the original values.
        """
        assert cfg.get_option("string", "option_text") == "beta"
        assert cfg.get_option("string", "option_text") != "alpha"
        cfg.reset_option("string", "option_text")
        assert cfg.get_option("string", "option_text") == "alpha"
        with pytest.raises(ValueError):
            cfg.reset_option("numeric", "integer_fixed")

        cfg.reset_options()
        assert cfg.show_options().shape[0] == 0
