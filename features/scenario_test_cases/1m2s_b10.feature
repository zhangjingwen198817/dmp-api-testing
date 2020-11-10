Feature: 1m2s_b10

  @case.1094 @version.09
  Scenario Outline: 1094-manual backup instance
    When I found 1m2s-B10 MySQL group with 3 MySQL instances,or I skip the test
    And I make a manual backup with <tool> in group
    Then the MySQL group manual backup list should contains the urman backup set in 1m
    Examples: manual backup tool
      | tool        |
      | Xtrabackup  |
      | mysqlbackup |

  @case.1115 @version.09
  Scenario: 1115-creat a backup rule
    When I found 1m2s-B10 MySQL group with 3 MySQL instances,or I skip the test
    And I found a MySQL instance without backup rule in the group, or I skip the test
    Then the backup dir of the MySQL instance should not exist
    When I add a backup rule to the MySQL instance, which will be triggered in 2m
    Then the response is ok
    And the MySQL instance should have a backup rule
    And the MySQL instance should have a new backup set in 3m in version 4

  @case.1121 @version.09
  Scenario: 1121-check the detail of the backup task
    When I found 1m2s-B10 MySQL group with 3 MySQL instances,or I skip the test
    When I found a MySQL instance with backup set in the group, or I skip the test
    And I check the detail of the backup task
    Then the detail of the backup task should be viewed

  @case.1118 @version.09
  Scenario: 1118-remove the backup rule
    When I found 1m2s-B10 MySQL group with 3 MySQL instances,or I skip the test
    And I found a MySQL instance with backup rule in the group, or I skip the test
    And I remove the backup rule
    Then the response is ok
    And the backup rule should not exist
    When I recycle the backup dir of the MySQL instance
    Then the response is ok
    And the backup dir of the MySQL instance should not exist

  @case.1098 @version.09
  Scenario: 1098-stop/start MySQL instance in group
    When I found 1m2s-B10 MySQL group with 3 MySQL instances,or I skip the test
    And I stop the MySQL instance in group
    And I start the MySQL instance in group
    When I stop MySQL instance ha enable
    Then the response is ok
    And MySQL instance ha enable should stopped in 1m