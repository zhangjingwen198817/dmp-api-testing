Feature: URDS

  Scenario: create zone
    When I want to create 3 zone on the urds

  Scenario: register sip
    When I found a lot of sip in DMP
    When I register the sips to urds


  Scenario: add a lot of sips to zone
    When I add sips to each zone

 
  Scenario: config sip to uproxy group in dmp
    When I found a lot of not sip uproxy group in dmp


 Scenario: register dmp uproxy to urds
    When I found a lot of uproxy group in dmp


  Scenario: Add uproxy to zone
    When I add a uproxy to each zone


  Scenario: add all dmp servrs to urds
    When I add all dmp server to urds


  Scenario: Add server to zone
    When I found a lot of valid servers on the urds


  Scenario: add template config
    When I add template from config
    Then the response is ok


  Scenario: add mysql instance
    When I add 600 mysql instance
    Then the response is ok


#  Scenario: approval mysql service
#     When I found a lot of mysql services

# @delsip
# Scenario: delete all sips
#   When I want delete all sips on the urds