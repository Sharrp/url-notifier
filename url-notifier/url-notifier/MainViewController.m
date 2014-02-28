//
//  MainViewController.m
//  url-notifier
//
//  Created by Anton Furin on 2/28/14.
//  Copyright (c) 2014 Anton Furin. All rights reserved.
//

#import "MainViewController.h"

@interface MainViewController ()

@end

@implementation MainViewController

- (id)initWithNibName:(NSString *)nibNameOrNil bundle:(NSBundle *)nibBundleOrNil
{
    self = [super initWithNibName:nibNameOrNil bundle:nibBundleOrNil];
    if (self) {
        // Custom initialization
    }
    return self;
}

- (void)viewDidLoad
{
    [super viewDidLoad];
    
    if (self.urlToOpen != nil)
    {
        [self openURL:self.urlToOpen];
    }
}

- (void)didReceiveMemoryWarning
{
    [super didReceiveMemoryWarning];
    // Dispose of any resources that can be recreated.
}

- (void) openURL:(NSURL *)url
{
    NSLog(@"Hey");
    if (![[UIApplication sharedApplication] openURL:url])
    {
        NSLog(@"Failed to open url: %@\n", url);
    }
}

@end
