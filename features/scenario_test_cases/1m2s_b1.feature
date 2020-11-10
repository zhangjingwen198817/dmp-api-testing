Feature: 1m2s_b1

  @case.1011 @version.09
  Scenario: 1011-add_group should succeed
    When I add a MySQL group
    Then the response is ok
    And the MySQL group list should contains the MySQL group

  @case.1017 @version.09
  Scenario: 1017-config the MySQL group with SIP
    When I found 1m2s-B1 MySQL group with 3 MySQL instances,or I skip the test
    Then the MySQL group should have sip
    When I execute the MySQL group "use mysql;drop table if exists test_group_sip;" with sip
    And I execute the MySQL group "create table mysql.test_group_sip(id int auto_increment not null primary key ,uname char(8));" with sip
    And I query the MySQL group "select table_name from information_schema.tables where table_name="test_group_sip";" with sip
    Then the MySQL response should be
      | table_name     |
      | test_group_sip |

    When I execute the MySQL group "use mysql;drop table if exists test_group_sip;" with sip

  @case.1137 @version.09
  Scenario: 1137-config the MySQL instance with SIP
    When I found 1m2s-B1 MySQL group with 3 MySQL instances,or I skip the test
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

  @case.1056 @version.09
  Scenario: 1056-reset MySQL instance in group
    When I found 1m2s-B1 MySQL group with 3 MySQL instances,or I skip the test
    And I reset MySQL instance in group

  @case.1096 @version.09
  Scenario: 1096-stop/start MySQL instance in group
    When I found 1m2s-B1 MySQL group with 3 MySQL instances,or I skip the test
    And I stop the MySQL instance in group
    And I start the MySQL instance in group


  @case.1133 @version.09
  Scenario: 1133-update MySQL user password
    When I found 1m2s-B1 MySQL group with 3 MySQL instances,or I skip the test
    And I found a server of the MySQL group's master instance
    And I found the password of the root user
    And I create MySQL user "test55" and grants "all privileges on *.*"
    Then the response is ok
    When I query the MySQL instance "show grants for 'test55';"
    Then the MySQL response should be
      | Grants for test55@%                         |
      | GRANT ALL PRIVILEGES ON *.* TO 'test55'@'%' |

    When I update MySQL user "test55" and password "test"
    Then the response is ok

    When I query the MySQL instance use user "test55" "show grants for 'test55';"
    Then the MySQL response should be
      | Grants for test55@%                         |
      | GRANT ALL PRIVILEGES ON *.* TO 'test55'@'%' |
