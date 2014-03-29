//
//  MainViewController.h
//  url-notifier
//
//  Created by Anton Furin on 2/28/14.
//  Copyright (c) 2014 Anton Furin. All rights reserved.
//

#import <UIKit/UIKit.h>

@interface MainViewController : UIViewController

@property (strong, nonatomic) NSURL *urlToOpen;
@property (strong, nonatomic) NSString *udid;

@property (nonatomic, strong) IBOutlet UILabel* udidStatusLabel;
@property (nonatomic, strong) IBOutlet UILabel* udidLabel;
@property (nonatomic, strong) IBOutlet UIActivityIndicatorView * udidActivityIndicator;
@property (nonatomic, strong) IBOutlet UILabel* contextHelpLabel;

- (void) openURL:(NSURL *)url;
- (void) requestLastUrl;

- (IBAction) helpButtonTap;

@end
