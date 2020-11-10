Feature: zone

    Scenario: add sip to zone
        When I found without sip of zone
        When I found a valid sip on urds
        When I add sip to zone
        Then the response is ok
        And  the zone should contain the sip

   Scenario: register a server
        When I register a server
        Then the response is ok
        And  the server list should contain the server

   Scenario: Add server to zone
      When I found a without 5 server zone
      When I found a server
      When I add the server to the zone
      Then the response is ok
      And the zone server list should contain the server

    Scenario: Add uproxy to zone
        When I found a without uproxy zone
        When I found a uproxy
        When I add a uproxy to the zone
        Then the response is ok
        And  the zone list should contain the uproxy


    Scenario: create mysql instance
        When I modify automatic approval config
        When I found mysql template class id
        When I found a valid zone on the urds
        When I add mysql instance
        Then the response is ok