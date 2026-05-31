def test_pytest_can_import_scripts_package():
    import scripts

    assert scripts.__name__ == "scripts"
