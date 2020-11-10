Feature: 1m2s_b12

  @case.1042_1 @version.09
  Scenario: 1042_1-stop SLA policy
    When I found 1m2s-B12 MySQL group with 3 MySQL instances,or I skip the test
    And the group SLA protocol should started, or I skip the test
    When I stop the group SLA protocol
    Then the response is ok
    Then the group SLA protocol should stopped

  @case.1042_2 @version.09
  Scenario: 1042_2-start SLA policy
    When I found 1m2s-B12 MySQL group with 3 MySQL instances,or I skip the test
    And the group SLA protocol should paused ,or I skip the test
    When I start the group SLA protocol
    Then the response is ok
    Then the group SLA protocol should started

  @case.1028 @version.09
  Scenario: 1028-config the MySQL group with SIP
    When I found 1m2s-B12 MySQL group with 3 MySQL instances,or I skip the test
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

  @case.1072 @version.09
  Scenario: 1072-config the MySQL instance with SIP
    When I found 1m2s-B12 MySQL group with 3 MySQL instances,or I skip the test
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
