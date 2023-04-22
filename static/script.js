function composeData(tweetText, imagePath, context, state) {
    const data = {
      post: {
        main: JSON.stringify({ text: tweetText }),
      },
      index: {
        post: JSON.stringify({ key: "main", value: { type: "md" } }),
      },
    };
  
    if (imagePath) {
      data.post.image = JSON.stringify({ path: imagePath });
    }
  
    const item = {
      type: "social",
      path: `${context.accountId}/post/main`,
    };
  
    const notifications = state.extractMentionNotifications(
      tweetText,
      item
    );
  
    if (notifications.length) {
      data.index.notify = JSON.stringify(
        notifications.length > 1 ? notifications : notifications[0]
      );
    }
  
    const hashtags = state.extractHashtags(tweetText);
  
    if (hashtags.length) {
      data.index.hashtag = JSON.stringify(
        hashtags.map((hashtag) => ({
          key: hashtag,
          value: item,
        }))
      );
    }
  
    return data;
  }
  
  function postToNear() {
    // Replace the tweetText and imagePath with your own variables or values
    const tweetText = "example tweet text";
    const imagePath = "path/to/image";
  
    // Call the composeData function to create the post data
    const postData = composeData(tweetText, imagePath, window.nearAPI, window.nearState);
  
    // Post the data to NEAR using the mob.near contract
    window.nearAPI.connection.signAndSendTransaction(
      'mob.near',
      [
        window.nearAPI.transactions.functionCall(
          'mob.near',
          'createPost',
          postData,
          300000000000000,
          '0'
        ),
      ],
      window.nearAPI.keyStores.InMemoryKeyStore.deserialize(
        window.localStorage.getItem('near-api-js:keystore')
      )
    );
  }
  
  
  
  console.log('Script loaded successfully!');
