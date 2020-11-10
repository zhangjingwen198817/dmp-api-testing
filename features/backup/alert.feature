Feature: alert

  Scenario Outline:Alert-001-add alert channel
    When I add <type> alert channel
    Then the response is ok
    And the alert channel list should contains the <type> alert channel
    Examples: channel type
	  | type |
	  | smtp  |
	  | wechat  |

  Scenario Outline:Alert-002-update alert channel
    When I found a valid the <type> alert channel, or I skip the test
    And I update the <type> alert channel
    Then the response is ok
    And the <type> alert channel should be updated
    Examples: channel type
	  | type |
	  | smtp  |
	  | wechat  |

  Scenario Outline: Alert-003-remove alert channel
    When I found a valid the <type> alert channel, or I skip the test
    And I remove the <type> alert channel
    Then the response is ok
    And the alert channel list should not contains the <type> alert channel

    Examples: channel type
	  | type |
	  | smtp  |
	  | wechat  |

  Scenario Outline: Alert-004-add alert configuration
    When I found a valid the <type> alert channel, or I skip the test
    And I add the <type> alert configuration
    Then the response is ok
    And the <type> alert configuration list should contains the alert configuration
    Examples: channel type
	  | type |
	  | smtp  |
	  | wechat  |

  Scenario Outline: Alert-005-update alert configuration
    When I found a valid the <type> alert configuration, or I skip the test
    And I update the <type> alert configuration
    Then the response is ok
    And the <type> alert configuration should be updated
    Examples: channel type
	  | type    |
	  | smtp    |
	  | wechat  |

  Scenario Outline: Alert-006-update alert configuration
    When I found a valid the <type> alert configuration, or I skip the test
    And I update the <type> alert configuration
    Then the response is ok
    And the <type> alert configuration should be updated
    Examples: channel type
	  | type    |
	  | smtp    |
	  | wechat  |

  Scenario Outline: Alert-007-remove alert configuration
    When I found a valid the <type> alert configuration, or I skip the test
    And I remove the <type> alert configuration
    Then the response is ok
    And the <type> alert configuration list should not contains the alert configuration
    Examples: channel type
	  | type    |
	  | smtp    |
	  | wechat  |
  Scenario Outline: Alert-008-add alert configuration subkey
    When I found a valid the <type> alert configuration, or I skip the test
    And I add the <type> alert configuration subkey
    Then the response is ok
    And the <type> alert configuration list should contains the alert configuration
    Examples: channel type
	  | type    |
	  | smtp    |
	  | wechat  |
