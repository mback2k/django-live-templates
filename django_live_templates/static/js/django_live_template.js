function LiveTemplates(socket, document) {
  var liveTemplatesClass = 'django-template-live';
  var liveTemplates = this;
  this.socket = socket;
  this.document = document;
  this.channels = [];
  this.listen = function (element) {
    var list = element.getElementsByClassName(liveTemplatesClass);
    for (var i = 0; i < list.length; i++) {
      var item = list[i];
      for (var j = 0; j < item.classList.length; j++) {
        var chan = item.classList[j];
        if (chan.lastIndexOf(liveTemplatesClass+'-', 0) === 0) {
          if (liveTemplates.channels.indexOf(chan) === -1) {
            liveTemplates.channels.push(chan);
            liveTemplates.socket.send(chan);
          };
        };
      };
    };
  };
  this.socket.onopen = function (event) {
    liveTemplates.listen(liveTemplates.document);
  };
  this.socket.onmessage = function (event) {
    var data = JSON.parse(event.data);
    if ('live_channel' in data) {
      var chan = data['live_channel'];
      if ('live_content' in data) {
        var list = liveTemplates.document.getElementsByClassName(chan);
        for (var i = 0; i < list.length; i++) {
          var item = list[i];
          item.outerHTML = data['live_content'];
          liveTemplates.listen(item);
        };
      } else {
        setTimeout(function(){
          liveTemplates.socket.send(chan);
        }, 60000);
      };
    };
  };
};
(function (window) {
  var protocol = window.location.protocol.replace('http', 'ws');
  var endpoint = '//' + window.location.host + '/ws/live/templates/';
  var socket = new WebSocket(protocol + endpoint);
  var engine = new LiveTemplates(socket, window.document);
})(window);