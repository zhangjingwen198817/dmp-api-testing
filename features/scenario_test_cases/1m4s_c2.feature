Feature: 1m4s_c2

  @case.1030 @version.09
  Scenario: 1030-config the MySQL group with SIP
    When I found 1m4s-C2 MySQL group with 5 MySQL instances,or I skip the test
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

  @case.1074 @version.09
  Scenario: 1074-config the MySQL instance with SIP
    When I found 1m4s-C2 MySQL group with 5 MySQL instances,or I skip the test
    Then the MySQL group should have sip
    When I execute the MySQL group "use mysql;drop table if exists test_group_sip;" with sip
    And I execute the MySQL group "create table mysql.test_group_sip(id int auto_increment not null primary key ,uname char(8));" with sip
    And I found a instance with a different sip in MySQL group
    Then the instance should have a different sip with the MySQL group
	When I query the MySQL instance "select table_name from information_schema.tables where table_name="test_group_sip";"
	Then the MySQL response should be
	  | table_name     |
	  | test_group_sip |

    When I execute the MySQL group "use mysql;drop table if exists test_group_sip;" with sip