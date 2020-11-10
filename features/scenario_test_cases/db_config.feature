Feature: db_config

  @case.dbc_1 @version.09
  Scenario Outline: update MySQL group configuration should succeed with socket
    When I found 1m1s-A1 MySQL group with 2 MySQL instances,or I skip the test
    Then I should get the config information of the MySQL group
    When I update MySQL group configuration "<option>" to "<option_value>" with socket
    Then the response is ok
    And the MySQL group configuration "<option>" should be "<option_value>" with socket in 1m
    When I found the master MySQL instance in the group
    And I query the MySQL instance "show global variables like '<option>'"
    Then the MySQL response should be
      | Variable_name | Value          |
      | <option>      | <option_value> |

    Examples:
      | option            | option_value |
      | slave_net_timeout | 180          |
      | slave_net_timeout | 120          |
      | slave_net_timeout | 60           |

  @case.dbc_2 @version.09
  Scenario Outline: update MySQL group configuration should succeed with server_addr
    When I found 1m1s-A1 MySQL group with 2 MySQL instances,or I skip the test
    Then I should get the config information of the MySQL group
    When I update MySQL group configuration "<option>" to "<option_value>" with server_addr
    Then the response is ok
    And the MySQL group configuration "<option>" should be "<option_value>" with server_addr in 1m
    When I found the master MySQL instance in the group
    And I query the MySQL instance "show global variables like '<option>'"
    Then the MySQL response should be
      | Variable_name | Value          |
      | <option>      | <option_value> |

    Examples:
      | option            | option_value |
      | slave_net_timeout | 180          |
      | slave_net_timeout | 120          |
      | slave_net_timeout | 60           |

  @case.dbc_3 @version.09
  Scenario Outline: update MySQL instance configuration should succeed with socket
    When I found 1m1s-A1 MySQL group with 2 MySQL instances,or I skip the test
    And I found a MySQL instance in the group
    Then I should get the config information of the MySQL instance
    When I update MySQL instance configuration "<option>" to "<option_value>" with socket
    Then the response is ok
    And the MySQL instance configuration "<option>" should be "<option_value>" with socket in 1m
    When I query the MySQL instance "show global variables like '<option>'"
    Then the MySQL response should be
      | Variable_name | Value          |
      | <option>      | <option_value> |

    Examples:
      | option            | option_value |
      | slave_net_timeout | 180          |
      | slave_net_timeout | 120          |
      | slave_net_timeout | 60           |

  @case.dbc_4 @version.09
  Scenario Outline: update MySQL instance configuration should succeed with server_addr
    When I found 1m1s-A1 MySQL group with 2 MySQL instances,or I skip the test
    And I found a MySQL instance in the group
    Then I should get the config information of the MySQL instance
    When I update MySQL instance configuration "<option>" to "<option_value>" with server_addr
    Then the response is ok
    And the MySQL instance configuration "<option>" should be "<option_value>" with server_addr in 1m
    When I query the MySQL instance "show global variables like '<option>'"
    Then the MySQL response should be
      | Variable_name | Value          |
      | <option>      | <option_value> |

    Examples:
      | option            | option_value |
      | slave_net_timeout | 180          |
      | slave_net_timeout | 120          |
      | slave_net_timeout | 60           |

  @case.export @version.09
  Scenario: export the MySQL group config
    When I found 1m1s-A1 MySQL group with 2 MySQL instances,or I skip the test
    And I export the MySQL group config
    Then the export is not empty
