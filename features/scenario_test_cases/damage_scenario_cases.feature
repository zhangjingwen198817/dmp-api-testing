Feature: damage environment

  #this case problem is sla_master_sequence and master_sequence different,or damage to the environment
  @case.1053 @case.1046 @version.09
  Scenario: 1053/1046-detach MySQL instance
    When I found 1m4s-C1 MySQL group with 5 MySQL instances,or I skip the test
    And I detach MySQL instance
    Then the response is ok
    And the MySQL instance should be not_exist in group

    When I takeover MySQL instance in group
    Then the MySQL instance should be exist in group
    When I enable the MySQL instance HA
    Then the response is ok
    And MySQL instance HA status should be running in 1m

  #this case problem is sla_master_sequence and master_sequence different,or damage to the environment
  @case.1045 @case.1052 @version.09
  Scenario: 1045/1052-takeover MySQL instance
    When I found 1m1s-A1 MySQL group with 2 MySQL instances,or I skip the test
    And I detach MySQL instance
    Then the response is ok
    And the MySQL instance should be not_exist in group

    When I takeover MySQL instance in group
    Then the MySQL instance should be exist in group
    When I enable the MySQL instance HA
    Then the response is ok
    And MySQL instance HA status should be running in 1m

#  @case.1180
#  Scenario: get inconsistent gtid sqls from slave
#    When I found 1m1s-A3 MySQL group with 2 MySQL instances,or I skip the test
#    And I update the instance read_only
#    Then I get inconsistent gtid sqls from slave

  @case.1055 @version.09
  Scenario: delete MySQL instance
    When I found 1m1s-A2 MySQL group with 2 MySQL instances,or I skip the test
    And I delete MySQL instance
    Then the MySQL instance list should not contains the MySQL instance

  @case.1057 @version.09
  Scenario: 1057-reset MySQL instance in group
    When I found 1m2s-B10 MySQL group with 3 MySQL instances,or I skip the test
    And I reset MySQL instance in group

  @case.1002 @version.09
  Scenario Outline: 1002-update server component
    When I found a server with component <component>, or I skip the test
    Then the component <component> should run with the pid in pidfile in 2m
    When I got the status of the component <component>
    And I update the server component <component> to version V9
    Then the response is ok
    And the server should has component <component>
    And the component <component> should run with the pid in pidfile in 2m
    And the version of the component <component> should be V9
    And the status of the component <component> should be the same with before in 2m

    Examples: install all components
      | component    |
      | udeploy      |
      | uguard-mgr   |
      | uguard-agent |
#      | umon         |
      | urman-mgr    |
      | urman-agent  |
      | uterm        |
      | usql         |

  @case.1004 @version.09
  Scenario Outline: 1004-uninstall all components
    When I found a server with component <component>, or I skip the test
    And I uninstall a component <component> on the server
    Then the response is ok
    Then the server should not has component <component>

    Examples: uninstall all components
      | component    |
      | udeploy      |
      | uguard-mgr   |
      | uguard-agent |
      | umon         |
      | urman-mgr    |
      | uterm        |
      | usql         |
      | urds         |

  @case.1004
  Scenario: 1004-uninstall  urman-agent
    When I found a server with component urman-agent, or I skip the test
    When I check the server have no backup rule, or I skip the case
    And I uninstall a component urman-agent on the server
    Then the response is ok
    Then the server should not has component urman-agent
