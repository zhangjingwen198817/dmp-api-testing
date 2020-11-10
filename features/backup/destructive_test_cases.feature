Feature: base cases.272

  @test @case.272
  Scenario: MySQL-001-database/stop MySQL service
    When I found a running MySQL instance, or I skip the test
    And I stop MySQL service
    Then the response is ok
    And stop MySQL service should succeed in 1m

  @test @case.272
  Scenario: MySQL-002-master-slave switching when kill three master pid
    When I found 1 MySQL groups with MySQL HA instances, or I skip the test
    And I found alert code "EXCLUDE_INSTANCE_SUCCESS", or I skip the test
    And I kill three master pid
    Then master-slave switching in 1m
    And expect alert code "EXCLUDE_INSTANCE_SUCCESS" in 2m

  @test
  Scenario: MySQL-003-database/takeover MySQL instance
    When I found 1 MySQL groups with MySQL HA instances, or I skip the test
    And I detach MySQL instance
    Then the response is ok

    Then the MySQL instance should be not exist
    When I takeover MySQL instance
    Then the response is ok
    And the MySQL instance should be listed

  @test
  Scenario: MySQL-004-components status when disable HA master-slave instance
    When I found 1 MySQL groups with MySQL HA instances, or I skip the test
    And I action stop role STATUS_MYSQL_SLAVE on HA instance
    Then the response is ok
    And the server uguard should running
    When I action stop role STATUS_MYSQL_MASTER on HA instance
    Then the response is ok
    And the server uguard should running