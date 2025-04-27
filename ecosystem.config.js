module.exports = {
    apps: [
      {
        name: 'process-csv',
        script: 'process.py',
        interpreter: 'py',
        watch: false
      },
      {
        name: 'send-second-message',
        script: 'second_message.py',
        interpreter: 'py',
        watch: false
      },
      {
        name: 'download-csv',
        script: 'download_csv.py',
        interpreter: 'py',
        watch: false,
        exec_mode: 'fork'
      }
    ]
  };