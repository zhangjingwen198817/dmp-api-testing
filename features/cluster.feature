Feature: dmp cluster
  This feature should only be used when installing DMP cluster

  Scenario: Init DMP
    When I init DMP
    Then the response is ok

  Scenario: Add server
    When I add server from parameter
    Then the response is ok

  Scenario: Install Udeploy,Uguard-agent,Urman-agent on all server
    When I install Udeploy,Uguard-agent,Urman-agent on all server

  Scenario: Install m-s MySQLs on all server
    When I found all server with components uguard-agent,urman-agent,ustats,udeploy, or I skip the test
    And I batch install the MySQL m-s instances
    Then the response is ok
    And the batch MySQL instance list should contains the MySQL instance in 60m

  Scenario: Install m-2s MySQLs on all server
    When I found all server with components uguard-agent,urman-agent,ustats,udeploy, or I skip the test
    And I batch install the MySQL m-2s instances
    Then the response is ok
    And the batch MySQL instance list should contains the MySQL instance in 60m

  Scenario: Add backup rules on all server
    When I batch add backup rules
    Then the response is ok