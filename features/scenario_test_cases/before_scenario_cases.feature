Feature: before scenario test cases
  @case.1177 @version.09
  Scenario: query from the slave replication relation
    When I found 1m4s-C1 MySQL group with 5 MySQL instances,or I skip the test
    And I query from the slave replication relation

  @case.1178 @version.09
  Scenario: get mysql tips by address
    When I found 1m1s-A3 MySQL group with 2 MySQL instances,or I skip the test
    And I get mysql tips by address
  @case.11179 @version.09
  Scenario: get hardware specifications
    When I found 1m1s-A1 MySQL group with 2 MySQL instances,or I skip the test
    And I get hardware specifications

  @case.1000-1 @version.09
  Scenario: 1000-1-add a server
    When I add a server
    Then the response is ok
    And the server should be in the server list

  @case.1000-2 @version.09
  Scenario: 1000-2-remove a server
    When I remove a server
    Then the response is ok
    And the server should not be in the server list

  @case.1001 @version.09
  Scenario Outline: 1001-server/install should install component
    When I found a server without component <component>, or I skip the test
    And I install a component <component> on the server
    Then the response is ok
    And the server should has component <component>
    And the server's component <component> should be installed as the standard

    Examples: install all components
      | component    |
      | udeploy      |
      | uguard-mgr   |
      | uguard-agent |
      | urman-mgr    |
      | urman-agent  |
      | uterm        |
      | usql         |
      | urds         |


  @case.1003_1 @version.09
  Scenario Outline: 1003_1-stop all components
    When I found a server with component <component>, or I skip the test
    And I action stop component <component>
    Then the response is ok
    And component <component> should stopped in 2m

    Examples: stop all components
      | component    |
      | udeploy      |
      | uguard-mgr   |
      | uguard-agent |
      | umon         |
      | urman-mgr    |
      | urman-agent  |
      | uterm        |
      | usql         |
      | urds         |

  @case.1003_2 @version.09
  Scenario Outline: 1003_2-start all components
    When I found a server with component <component>, or I skip the test
    And I action start component <component>
    Then the response is ok
    And component <component> should started in 2m

    Examples: start all components
      | component    |
      | udeploy      |
      | uguard-mgr   |
      | uguard-agent |
      | umon         |
      | urman-mgr    |
      | urman-agent  |
      | uterm        |
      | usql         |
      | urds         |

  @case.1005 @version.09
  Scenario: 1005-view detail of component
    When I get the list of servers,through version 5
    Then the response is ok
    And I check the version information for all components

  @case.1150 @version.09
  Scenario: 1150-update a tag in tag_pool
    When I create a tag in tag pool with attribute tag01
    Then the response is ok
    And the tag should be in the tag pool
    When I update the tag to a new one in 1m
    Then the response is ok
    And the tag should be in the tag pool

  @case.1151 @version.09
  Scenario: 1151-update the sip for the umc
    When I found a valid SIP, or I skip the test
    And I update the sip for the umc with id umc
    Then the response is ok
    And the umc sip should in the sip list