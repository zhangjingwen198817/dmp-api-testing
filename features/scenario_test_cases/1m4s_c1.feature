Feature: 1m4s_c1

  @case.1029 @version.09
  Scenario: 1029-config the MySQL group with SIP
    When I found 1m4s-C1 MySQL group with 5 MySQL instances,or I skip the test
    Then the MySQL group should have sip
    When I execute the MySQL group "use mysql;drop table if exists test_group_sip;" with sip
    And I execute the MySQL group "create table mysql.test_group_sip(id int auto_increment not null primary key ,uname char(8));" with sip
    And I query the MySQL group "select table_name from information_schema.tables where table_name="test_group_sip";" with sip
    Then the MySQL response should be
      | table_name     |
      | test_group_sip |
    When I execute the MySQL group "use mysql;drop table if exists test_group_sip;" with sip


  @case.1073 @version.09
  Scenario: 1073-config the MySQL instance with SIP
    When I found 1m4s-C1 MySQL group with 5 MySQL instances,or I skip the test
    Then the MySQL group should have sip
    When I execute the MySQL group "use mysql;drop table if exists test_group_sip;" with sip
    And I execute the MySQL group "create table mysql.test_group_sip(id int auto_increment not null primary key ,uname char(8));" with sip
    And I found a instance with a similar sip in MySQL group
    Then the instance should have a similar sip with the MySQL group
    When I query the MySQL instance "select table_name from information_schema.tables where table_name="test_group_sip";"
    Then the MySQL response should be
      | table_name     |
      | test_group_sip |
    When I execute the MySQL group "use mysql;drop table if exists test_group_sip;" with sip

  @case.1092 @version.09
  Scenario: 1092-pause HA and stop copying
    When I found 1m4s-C1 MySQL group with 5 MySQL instances,or I skip the test
    And I pause HA and stop copying the MySQL instance in group
    Then the MySQL instance STATUS_MYSQL_REPL_BAD and MANUAL_EXCLUDE_HA should be stopped in 1m

    When I enable the MySQL instance HA
    Then the response is ok
    And MySQL instance HA status should be running in 1m

  @case.1095 @version.09
  Scenario Outline: 1095-manual backup instance
    When I found 1m4s-C1 MySQL group with 5 MySQL instances,or I skip the test
    And I make a manual backup with <tool> in group
    Then the MySQL group manual backup list should contains the urman backup set in 1m
    Examples: manual backup tool
      | tool        |
      | Xtrabackup  |
      | mysqlbackup |

  @case.1099 @version.09
  Scenario: 1099-stop/start MySQL instance in group
    When I found 1m4s-C1 MySQL group with 5 MySQL instances,or I skip the test
    And I stop the MySQL instance in group
    And I start the MySQL instance in group

  @case.1058 @version.09
  Scenario: 1058-reset MySQL instance in group
    When I found 1m4s-C1 MySQL group with 5 MySQL instances,or I skip the test
    And I reset MySQL instance in group


  @case.1100-1 @version.09
  Scenario: 1100-1-add a tag to the instance
    When I create a tag in tag pool with attribute instance
    Then the response is ok
    And the tag should be in the tag pool
    When I found 1m4s-C1 MySQL group with 5 MySQL instances,or I skip the test
    And I add a tag to the instance
    Then the response is ok
    And the tag should be in the instance tag list

  @case.1100-2 @version.09
  Scenario: 1100-2-remove the tag from the instance
    When I found a instance with tag attributed instance
    And I remove the tag from the instance
    Then the response is ok
    And the tag should not be in the instance tag list

  @case.1116 @version.09
  Scenario: 1116-creat a backup rule
    When I found 1m4s-C1 MySQL group with 5 MySQL instances,or I skip the test
    And I found a MySQL instance without backup rule in the group, or I skip the test
    Then the backup dir of the MySQL instance should not exist
    When I add a backup rule to the MySQL instance, which will be triggered in 2m
    Then the response is ok
    And the MySQL instance should have a backup rule
    And the MySQL instance should have a new backup set in 3m in version 4

  @case.1122 @version.09
  Scenario: 1122-check the detail of the backup task
    When I found 1m4s-C1 MySQL group with 5 MySQL instances,or I skip the test
    When I found a MySQL instance with backup set in the group, or I skip the test
    And I check the detail of the backup task
    Then the detail of the backup task should be viewed

  @case.1119 @version.09
  Scenario: 1119-remove the backup rule
    When I found 1m4s-C1 MySQL group with 5 MySQL instances,or I skip the test
    And I found a MySQL instance with backup rule in the group, or I skip the test
    And I remove the backup rule
    Then the response is ok
    And the backup rule should not exist
    When I recycle the backup dir of the MySQL instance
    Then the response is ok
    And the backup dir of the MySQL instance should not exist
