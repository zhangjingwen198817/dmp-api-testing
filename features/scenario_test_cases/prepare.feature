Feature: prepare
  
  Scenario: prepare DMP environment
    When I prepare 33 agent environment
    And I prepare 3 mgr environment

  Scenario: prepare valid ips to sip pool
    When I add the ip to sip pool
    Then the response is ok
    Then the sip pool should contain the added IP

  @case.1001 @version.09
  Scenario: 1001-server/install should install umon
    When I found a server without component umon, or I skip the test
    And I install a component umon on the server
    Then the response is ok
    And the server should has component umon
    And the server's component umon should be installed as the standard


  @case.1044 @case.1048 @case.1049 @case.1050 @version.09
  Scenario: 1044/1048-prepare MySQL group and instance
    When I found all server with components uguard-agent,urman-agent,ustats,udeploy, or I skip the test
    And I prepare 3 group MySQL m-ns 2 instances use 3000 in a

    When I found all server with components uguard-agent,urman-agent,ustats,udeploy, or I skip the test
    And I prepare 6 group MySQL m-ns 3 instances use 4000 in b
    When I found all server with components uguard-agent,urman-agent,ustats,udeploy, or I skip the test
    And I prepare 5 group MySQL m-ns 3 instances use 5000 in b6

    And I prepare 1 group 1m2s off-standard MySQL instances

    When I found all server with components uguard-agent,urman-agent,ustats,udeploy, or I skip the test
    When I add 5 group MySQL m-ns 5 instances use 3306 in c

  Scenario: config all MySQL group
    Given I config the installed MySQL group and instance

