# Created by lxl at 2019/7/25
Feature: MongoDB test

  @case.1151 @version.09
  Scenario: add MongoDB group should succeed
    When I found a valid port, or I skip the test
    And I add MongoDB group
    Then the response is ok
    And the MongoDB group list should contains the MongoDB group

  @case.1152 @version.09
  Scenario: add MongoDB instance should succeed
    When I found a server with components ustats,udeploy,uguard-agent,urman-agent, or I skip the test
    And I found a MongoDB group without MongoDB instance, or I skip the test
    And I add MongoDB master instance
    Then the MongoDB instance should add succeed in 1m

    When I found all server with components uguard-agent,urman-agent,ustats,udeploy, or I skip the test
    And I add MongoDB slave instance
    Then the MongoDB group should have 1 running MongoDB master and 1 running MongoDB slave in 1m

  @case.1153 @version.09
  Scenario: stop and start MongoDB instance should succeed
    When I found a running MongoDB instance slave, or I skip the test
    And I action stop the MongoDB instance
    Then the response is ok
    And the MongoDB instance should stopped in 2m

    When I action start the MongoDB instance
    Then the response is ok
    And the MongoDB instance should started in 2m

  @case.1154 @version.09
  Scenario: remove MongoDB instance should succeed
    When I found a running MongoDB instance slave, or I skip the test
    And I remove MongoDB instance
    Then the response is ok
    And the MongoDB instance list should not contains the MongoDB instance in 2m