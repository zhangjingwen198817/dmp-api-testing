Feature: 1m2s_b3

  @case.1038_1 @version.09
  Scenario: 1038_1-stop SLA policy
    When I found 1m2s-B3 MySQL group with 3 MySQL instances,or I skip the test
    And the group SLA protocol should started, or I skip the test
    When I stop the group SLA protocol
    Then the response is ok
    Then the group SLA protocol should stopped

  @case.1038_2 @version.09
  Scenario: 1038_2-start SLA policy
    When I found 1m2s-B3 MySQL group with 3 MySQL instances,or I skip the test
    And the group SLA protocol should paused ,or I skip the test
    When I start the group SLA protocol
    Then the response is ok
    Then the group SLA protocol should started

  @case.1019 @version.09
  Scenario: 1019-config the MySQL group with SIP
    When I found 1m2s-B3 MySQL group with 3 MySQL instances,or I skip the test
    Then the MySQL group should have sip
    When I execute the MySQL group "use mysql;drop table if exists test_group_sip;" with sip
    And I execute the MySQL group "create table mysql.test_group_sip(id int auto_increment not null primary key ,uname char(8));" with sip
    And I query the MySQL group "select table_name from information_schema.tables where table_name="test_group_sip";" with sip
    Then the MySQL response should be
      | table_name     |
      | test_group_sip |

    When I execute the MySQL group "use mysql;drop table if exists test_group_sip;" with sip

  @case.1064 @version.09
  Scenario: 1064-config the MySQL instance with SIP
    When I found 1m2s-B3 MySQL group with 3 MySQL instances,or I skip the test
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

  @case.1093 @version.09
  Scenario Outline: 1093-manual backup instance
    When I found 1m2s-B3 MySQL group with 3 MySQL instances,or I skip the test
    And I make a manual backup with <tool> in group
    Then the MySQL group manual backup list should contains the urman backup set in 1m
    Examples: manual backup tool
      | tool        |
      | Xtrabackup  |
      | mysqlbackup |

  @case.1081 @version.09
  Scenario: 1081-promote the slave instance to master
    When I found 1m2s-B3 MySQL group with 3 MySQL instances,or I skip the test
    And I promote the slave instance to master
    Then promote slave instance to master should succeed in 1m


  @case.1097 @version.09
  Scenario: 1097-stop/start MySQL instance in group
    When I found 1m2s-B3 MySQL group with 3 MySQL instances,or I skip the test
    And I stop the MySQL instance in group
    And I start the MySQL instance in group