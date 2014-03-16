//
//  AppDelegate.m
//  url-notifier
//
//  Created by Anton Furin on 2/28/14.
//  Copyright (c) 2014 Anton Furin. All rights reserved.
//

#import "AppDelegate.h"

#import "NSData+NSData_Conversion.h"

@implementation AppDelegate

- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions
{
    self.window = [[UIWindow alloc] initWithFrame:[[UIScreen mainScreen] bounds]] ;
    
    self.mainVC = [[MainViewController alloc] initWithNibName:@"MainViewController" bundle:nil];
    NSDictionary *payload = [launchOptions objectForKey:UIApplicationLaunchOptionsRemoteNotificationKey];
    NSLog(@"Payload: %@", payload);
    if (payload != nil && payload[@"url"] != nil)
    {
        self.mainVC.urlToOpen = [NSURL URLWithString:payload[@"url"]];
    }
    UINavigationController *nav = [[UINavigationController alloc]  initWithRootViewController:self.mainVC];
    
    self.window.rootViewController = nav;
    [self.window makeKeyAndVisible];
    
    // Override point for customization after application launch.
    [[UIApplication sharedApplication] registerForRemoteNotificationTypes:
     (UIRemoteNotificationTypeSound | UIRemoteNotificationTypeAlert)];
    
    return YES;
}

- (void)application:(UIApplication *)application didReceiveRemoteNotification:(NSDictionary *)userInfo
{
    NSLog(@"User info: %@", userInfo);
    if (userInfo != nil && userInfo[@"url"] != nil)
    {
        [self.mainVC openURL:[NSURL URLWithString:userInfo[@"url"]]];
    }
}

- (void)application:(UIApplication*)application didRegisterForRemoteNotificationsWithDeviceToken:(NSData*)deviceToken
{
    NSData *lastToken = (NSData *)[[NSUserDefaults standardUserDefaults] objectForKey:@"last_token"];
    if (!lastToken || ![deviceToken isEqualToData:lastToken])
    {
        NSString *did = [[[UIDevice currentDevice] identifierForVendor] UUIDString];
        NSString *strToken = [deviceToken hexadecimalString];
        NSString* jsonData = [NSString stringWithFormat:@"{\"did\":\"%@\", \"token\":\"%@\"}", did, strToken];
        
        // Send token to server
        NSURL *requestURL = [NSURL URLWithString:@"http://188.226.174.130:5000/device/"];
        NSMutableURLRequest *request = [NSMutableURLRequest requestWithURL:requestURL];
        request.HTTPMethod = @"POST";
        [request setValue:@"application/json" forHTTPHeaderField:@"Content-Type"];
        request.HTTPBody = [jsonData dataUsingEncoding:NSUTF8StringEncoding];
        
        NSOperationQueue *queue = [[NSOperationQueue alloc] init];
        [NSURLConnection sendAsynchronousRequest:request
                                           queue:queue
                               completionHandler:^(NSURLResponse* response, NSData* data, NSError* error){
                                   if ([data length] > 0 && error == nil)
                                   {
                                       NSString *udid = [[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding];
                                       NSLog(@"Received data: %@", udid);
                                       [[NSUserDefaults standardUserDefaults] setObject:udid forKey:@"udid"];
                                       [[NSUserDefaults standardUserDefaults] setObject:deviceToken forKey:@"last_token"];
                                       [[NSUserDefaults standardUserDefaults] synchronize];
                                       [[NSNotificationCenter defaultCenter] postNotificationName:@"udid update"
                                                                                           object:udid];
                                   }
                                   else
                                   {
                                       NSLog(@"Error on sending token: %@", error);
                                   }
                               }];
        
    }
}

- (void)application:(UIApplication*)application didFailToRegisterForRemoteNotificationsWithError:(NSError*)error
{
	NSLog(@"Failed to get token, error: %@", error);
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
