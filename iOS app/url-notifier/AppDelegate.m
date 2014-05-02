//
//  AppDelegate.m
//  url-notifier
//
//  Created by Anton Furin on 2/28/14.
//  Copyright (c) 2014 Anton Furin. All rights reserved.
//

#import "AppDelegate.h"

@implementation AppDelegate

- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions
{
    self.window = [[UIWindow alloc] initWithFrame:[[UIScreen mainScreen] bounds]] ;
    
    self.mainVC = [[MainViewController alloc] initWithNibName:@"MainViewController" bundle:nil];
    NSDictionary *payload = launchOptions[UIApplicationLaunchOptionsRemoteNotificationKey];
    NSLog(@"Payload: %@", payload);
    if (payload != nil && payload[@"url"] != nil)
    {
        self.mainVC.urlStringToOpen = payload[@"url"];
    }
    UINavigationController *nav = [[UINavigationController alloc]  initWithRootViewController:self.mainVC];
    nav.navigationBarHidden = YES;
    self.window.rootViewController = nav;
    [self.window makeKeyAndVisible];
    
    // Override point for customization after application launch.
    [[UIApplication sharedApplication] registerForRemoteNotificationTypes:
     (UIRemoteNotificationTypeSound | UIRemoteNotificationTypeAlert)];
    [UIApplication sharedApplication].applicationIconBadgeNumber = 0;
    
    return YES;
}

- (void)application:(UIApplication *)application didReceiveRemoteNotification:(NSDictionary *)userInfo
{
    [UIApplication sharedApplication].applicationIconBadgeNumber = 0;
    NSLog(@"User info: %@", userInfo);
    NSNumber *len = userInfo[@"len"];
    NSString *url = userInfo[@"url"];
    
    // Checking that we've got full url
    if (userInfo && url && len && [len integerValue] == [url length])
    {
        [self.mainVC openURL:userInfo[@"url"]];
    }
    else
    {
        [self.mainVC requestLastUrl];
    }
}

- (void)application:(UIApplication*)application didRegisterForRemoteNotificationsWithDeviceToken:(NSData*)deviceToken
{
    NSData *lastToken = (NSData *)[[NSUserDefaults standardUserDefaults] objectForKey:@"last_token"];
    NSLog(@"Token: %@", deviceToken);
    if (!lastToken || ![deviceToken isEqualToData:lastToken] || !self.mainVC.udid)
    {
        [[NSUserDefaults standardUserDefaults] setObject:deviceToken forKey:@"last_token"];
        [[NSUserDefaults standardUserDefaults] synchronize];
        [self.mainVC tokenUpdated];
    }
}

- (void)application:(UIApplication*)application didFailToRegisterForRemoteNotificationsWithError:(NSError*)error
{
    NSLog(@"%@", error);
    [self.mainVC tokenUpdateFailed];
}

#pragma mark -- App state methods

- (void)applicationWillResignActive:(UIApplication *)application
{
    // Sent when the application is about to move from active to inactive state. This can occur for certain types of temporary interruptions (such as an incoming phone call or SMS message) or when the user quits the application and it begins the transition to the background state.
    // Use this method to pause ongoing tasks, disable timers, and throttle down OpenGL ES frame rates. Games should use this method to pause the game.
}

- (void)applicationDidEnterBackground:(UIApplication *)application
{
    // Use this method to release shared resources, save user data, invalidate timers, and store enough application state information to restore your application to its current state in case it is terminated later. 
    // If your application supports background execution, this method is called instead of applicationWillTerminate: when the user quits.
}

- (void)applicationWillEnterForeground:(UIApplication *)application
{
    // Called as part of the transition from the background to the inactive state; here you can undo many of the changes made on entering the background.
    [self.mainVC enterForeground];
}

- (void)applicationDidBecomeActive:(UIApplication *)application
{
    // Restart any tasks that were paused (or not yet started) while the application was inactive. If the application was previously in the background, optionally refresh the user interface.
}

- (void)applicationWillTerminate:(UIApplication *)application
{
    // Called when the application is about to terminate. Save data if appropriate. See also applicationDidEnterBackground:.
}

@end
