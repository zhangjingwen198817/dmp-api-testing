Feature: uproxy


  @case.1156 @version.09
  Scenario: add Uproxy group should succeed
    When I found a valid port, or I skip the test
    And I add Uproxy group
    Then the response is ok
    And the Uproxy group list should contains the Uproxy group


  @case.1157 @version.09
  Scenario: add Uproxy m-s instances should succeed
    When I found a Uproxy group without Uproxy instance, or I skip the test
    And I found a server without Uproxy instance
    And I add Uproxy instance
    Then the response is ok
    And the Uproxy group should have 1 running Uproxy instance in 1m

    When I found a valid port, or I skip the test
    And I found a server without Uproxy instance
    And I add Uproxy instance
    Then the response is ok
    And the Uproxy group should have 2 running Uproxy instance in 1m


  @case.1158 @version.09
  Scenario: add Uproxy router should succeed
    When I found 1 Uproxy group with Uproxy instance, or I skip the test
    And I add Uproxy router
    Then the response is ok
    And the Uproxy router list should contains the Uproxy router


  @case.1159 @version.09
  Scenario: add Uproxy router backend should succeed
    When I found 1 Uproxy router, or I skip the test
    And I found 1m1s-A1 MySQL group with 2 MySQL instances,or I skip the test
    And I add Uproxy router backend
    Then the response is ok
    And the Uproxy router backend list should contains the backend


  @case.1160 @version.09
  Scenario: uproxy_backend list
    When I found a Uproxy router with backend instance,or I skip the test
    And I get uproxy_backend list, page size is 1, page index is 2
    Then the response is ok
    And the list should not None

  @case.1161 @version.09
  Scenario: uproxy_pool list
    When I found a Uproxy router with backend instance,or I skip the test
    And I get uproxy_pool list, page size is 1, page index is 2
    Then the response is ok
    And the list should not None

  @case.1162 @version.09
  Scenario: uproxy_statistic list
    When I found a Uproxy router with backend instance,or I skip the test
    And I get uproxy_statistic list, page size is 1, page index is 2
    Then the response is ok
    And the list should not None


  @case.1163 @version.09
  Scenario: remove backend instance should succeed
    When I found a Uproxy router with backend instance,or I skip the test
    And I remove all backend instance
    Then the response is ok
    And the Uproxy router should not contains any backend instance in 1m


  @case.1164 @version.09
  Scenario: remove Uproxy router should succeed
    When I found 1 Uproxy router without backend instance, or I skip the test
    And I remove the Uproxy router
    Then the response is ok
    And Uproxy router should not contains the Uproxy router in 1m


  @case.1165 @version.09
  Scenario: remove Uproxy instance should succeed
    When I found 1 Uproxy group with Uproxy instance, or I skip the test
    And I remove all Uproxy instance
    Then the response is ok
    And the Uproxy group should not contains any Uproxy instance in 1m

  @case.1166 @version.09
  Scenario: remove Uproxy group should succeed
    When I found a Uproxy group without Uproxy instance, or I skip the test
    And I remove the Uproxy group
    Then the response is ok
    And the Uproxy group list should not contains the Uproxy group
