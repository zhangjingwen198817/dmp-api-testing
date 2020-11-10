Feature: 1m1s_a1

  @case.1010 @version.09
  Scenario: 1010-add_group should succeed
    When I add a MySQL group
    Then the response is ok
    And the MySQL group list should contains the MySQL group

  @case.1013 @version.09
  Scenario: 1013-remove_group should succeed
    When I found a MySQL group without MySQL instance, or I skip the test
    And I remove the MySQL group
    Then the response is ok
    And the MySQL group list should not contains the MySQL group

  @case.1014 @version.09
  Scenario: 1014-config the MySQL group with SIP
    When I found 1m1s-A1 MySQL group with 2 MySQL instances,or I skip the test
    And I prepare the group with sip if not exists
    Then the response is ok
    And the MySQL group should have sip
    When I execute the MySQL group "use mysql;drop table if exists test_group_sip;" with sip
    And I execute the MySQL group "create table mysql.test_group_sip(id int auto_increment not null primary key ,uname char(8));" with sip
    And I query the MySQL group "select table_name from information_schema.tables where table_name="test_group_sip";" with sip
    Then the MySQL response should be
      | table_name     |
      | test_group_sip |
    When I execute the MySQL group "use mysql;drop table if exists test_group_sip;" with sip
    And I remove the sip for the MySQL group
    Then the response is ok
    And the MySQL group should not have sip

  @case.1060 @version.09
  Scenario: 1060-config the MySQL instance with SIP
    When I found 1m1s-A1 MySQL group with 2 MySQL instances,or I skip the test
    And I found a MySQL master instance in the group
    And I prepare the instance with sip if not exists
    Then the response is ok
    And the MySQL master instance should have sip

    When I found a MySQL slave instance in the group
    And I prepare the instance with sip if not exists
    Then the response is ok
    And the MySQL slave instance should have sip

    When I remove the sip for the MySQL master instance
    Then the response is ok
    And the MySQL master instance should not have sip
    When I remove the sip for the MySQL slave instance
    Then the response is ok
    And the MySQL slave instance should not have sip
    And the MySQL group 1m1s-A1 with 2 MySQL instances should back to normal

  @case.1080 @version.09
  Scenario: 1080-disable/enable the MySQL instance HA
    When I found 1m1s-A1 MySQL group with 2 MySQL instances,or I skip the test
    And I disable the MySQL instance HA in group
    Then MySQL instance ha enable should stopped in 1m

    When I enable the MySQL instance HA in group
    Then MySQL instance HA status should be running in 1m

  @case.1114 @version.09
  Scenario: 1114-creat a backup rule
    When I found 1m1s-A1 MySQL group with 2 MySQL instances,or I skip the test
    And I found a MySQL instance without backup rule in the group, or I skip the test
    Then the backup dir of the MySQL instance should not exist
    When I add a backup rule to the MySQL instance, which will be triggered in 2m
    Then the response is ok
    And the MySQL instance should have a backup rule
    And the MySQL instance should have a new backup set in 3m in version 4

  @case.1120 @version.09
  Scenario: 1120-check the detail of the backup task
    When I found 1m1s-A1 MySQL group with 2 MySQL instances,or I skip the test
    When I found a MySQL instance with backup set in the group, or I skip the test
    And I check the detail of the backup task
    Then the detail of the backup task should be viewed

  @case.1117 @version.09
  Scenario: 1117-remove the backup rule
    When I found 1m1s-A1 MySQL group with 2 MySQL instances,or I skip the test
    And I found a MySQL instance with backup rule in the group, or I skip the test
    And I remove the backup rule
    Then the response is ok
    And the backup rule should not exist
    When I recycle the backup dir of the MySQL instance
    Then the response is ok
    And the backup dir of the MySQL instance should not exist

  @case.1131 @version.09
  Scenario: 1131-stop delay detection
    When I found 1m1s-A1 MySQL group with 2 MySQL instances,or I skip the test
    And I stop delay detection
    Then the response is ok
    And stop delay detection should succeed in 1m

    When I start delay detection
    Then the response is ok
    And start delay detection should succeed in 1m

  @case.1132 @version.09
  Scenario: 1132-stop/start monitoring
    When I found 1m1s-A1 MySQL group with 2 MySQL instances,or I skip the test
    And I stop monitoring
    Then the response is ok
    And stop monitoring should succeed in 1m

    When I start monitoring
    Then the response is ok
    And start monitoring should succeed in 1m

  @case.1134 @version.09
  Scenario: 1134-upgrade MySQL instance
    When I found 1m1s-A1 MySQL group with 2 MySQL instances,or I skip the test
    And I upgrade MySQL instance with mysql-5.7.25-linux-glibc2.12-x86_64.tar.gz
    Then the MySQL instance upgrade to mysql-5.7.25-linux-glibc2.12-x86_64.tar.gz should succeed 	


