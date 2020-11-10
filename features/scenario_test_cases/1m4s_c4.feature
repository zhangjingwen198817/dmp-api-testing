Feature: 1m4s_c4

  @case.1043_1 @version.09
  Scenario: 1043_1-stop SLA policy
    When I found 1m4s-C4 MySQL group with 5 MySQL instances,or I skip the test
    And the group SLA protocol should started, or I skip the test
    When I stop the group SLA protocol
    Then the response is ok
    Then the group SLA protocol should stopped

  @case.1043_1 @version.09
  Scenario: 1043_1-start SLA policy
    When I found 1m4s-C4 MySQL group with 5 MySQL instances,or I skip the test
    And the group SLA protocol should paused ,or I skip the test
    When I start the group SLA protocol
    Then the response is ok
    Then the group SLA protocol should started

  @case.1032 @version.09
  Scenario: 1032-config the MySQL group with SIP
    When I found 1m4s-C4 MySQL group with 5 MySQL instances,or I skip the test
    Then the MySQL group should have sip
    When I execute the MySQL group "use mysql;drop table if exists test_group_sip;" with sip
    And I execute the MySQL group "create table mysql.test_group_sip(id int auto_increment not null primary key ,uname char(8));" with sip
    And I query the MySQL group "select table_name from information_schema.tables where table_name="test_group_sip";" with sip
    Then the MySQL response should be
      | table_name     |
      | test_group_sip |
    When I found a instance with a different sip in MySQL group
    Then the instance should have a different sip with the MySQL group
    When I query the MySQL instance "select table_name from information_schema.tables where table_name="test_group_sip";"
    Then the MySQL response should be
      | table_name     |
      | test_group_sip |
    When I execute the MySQL group "use mysql;drop table if exists test_group_sip;" with sip

  @case.1059 @version.09
  Scenario: 1059-reset MySQL instance in group
    When I found 1m4s-C4 MySQL group with 5 MySQL instances,or I skip the test
    And I reset MySQL instance in group

  @case.1076 @version.09
  Scenario: 1076-config the MySQL instance with SIP
    When I found 1m4s-C4 MySQL group with 5 MySQL instances,or I skip the test
    Then the MySQL group should have sip
    When I execute the MySQL group "use mysql;drop table if exists test_group_sip;" with sip
    And I execute the MySQL group "create table mysql.test_group_sip(id int auto_increment not null primary key ,uname char(8));" with sip
    And I found a instance with a different sip in MySQL group
    Then the instance should have a different sip with the MySQL group
    When I query the MySQL instance "select table_name from information_schema.tables where table_name="test_group_sip";"
    Then the MySQL response should be
      | table_name     |
      | test_group_sip |

  @case.1085 @version.09
  Scenario: 1085-promote the slave instance to master
    When I found 1m4s-C4 MySQL group with 5 MySQL instances,or I skip the test
    And I promote the slave instance to master
    Then promote slave instance to master should succeed in 1m