let uploadFiles = [];
let uploadURL = window.location.href;
let uploadChunkSize = 2097152;  // 2MB
let placeholderIcon = 'https://placehold.co/60x60';

class ChunkUploaded {
    constructor(URL = null, chunkSize = null, placeholderIcon = null) {
        this.URL = URL
        this.chunkSize = chunkSize
        this.placeholderIcon = placeholderIcon
    }

    init() {
        if (this.URL && typeof this.URL === 'string') {
            uploadURL = this.URL;
        }
        if (this.chunkSize) {
            if (typeof this.chunkSize === 'string') {
                this.chunkSize = parseInt(this.chunkSize);
            }

            if (typeof this.chunkSize === 'number' && !isNaN(this.chunkSize)) {
                uploadChunkSize = this.chunkSize;
            }
        }
        if (this.placeholderIcon && this.placeholderIcon === 'string') {
            placeholderIcon = this.placeholderIcon;
        }
    }
}

function getFormData(evt) {
    return new FormData($(evt.target)[0]);
}

function uploadFile(evt, file, chunkFrom = 0, chunkSize = 2097152) {
    let isEOF = 'false';
    let chunkTo = chunkFrom + chunkSize + 1;
    let blob = file.slice(chunkFrom, chunkTo);
    if (chunkTo >= file.size) {
        isEOF = 'true';
    }
    let formData = getFormData(evt);
    formData.append('action', $(evt.originalEvent.submitter).attr('name'));
    formData.append('file', blob, file.name);
    $.ajaxSetup({
        headers: {
            "X-CSRFToken": getDjangoCookie(),
            "X-File-ID": getHiddenInputChecksum(),
            "X-File-Name": file.name,
            "X-File-Checksum": file.checksum,
            "X-File-Chunk-From": chunkFrom,
            "X-File-Chunk-Size": chunkSize,
            "X-File-Chunk-To": chunkTo,
            "X-File-EOF": isEOF,
            "X-File-Size": file.size,
            "X-File-MimeType": file.type,
        }
    });

    $.ajax({
        xhr: function () {
            const xhr = new XMLHttpRequest();
            xhr.upload.addEventListener('progress', function (e) {
                if (e.lengthComputable) {
                    let percent = Math.round(((chunkFrom + blob.size) / file.size) * 100);
                    if (file.size < chunkSize) {
                        percent = Math.round((e.loaded / e.total) * 100);
                    }
                    updateProgressBar(file.checksum, percent)
                }
            });
            return xhr;
        },

        url: uploadURL,
        type: 'POST',
        dataType: 'json',
        cache: false,
        processData: false,
        contentType: false,
        data: formData,
        error: function (response) {
            console.log(response)
            let errorMessage = response.statusText;
            if (response.responseJSON) {
                errorMessage = response.responseJSON.message;
                if (response.responseJSON.errors && Array.isArray(response.responseJSON.errors) && response.responseJSON.errors.length > 0) {
                    updateError(evt, response.responseJSON.errors)
                }
            }
            updateStatus(file.checksum, errorMessage, 'danger');
            toastr.error(`Failed to upload file: ${file.name}.`);
            updateProgressBar(file.checksum, 100, '#dc3545');
        },
        success: function (response) {
            if (chunkTo < file.size) {
                updateStatus(file.checksum, response.message, 'warning');
                uploadFile(evt, file, chunkTo, chunkSize);
            } else {
                updateStatus(file.checksum, response.message, 'success');
                 [...$('.file-item')].forEach((node) => {
                    if (node.id === file.checksum) {
                        const viewedObj = $(node).find('.viewed a');
                        viewedObj.attr('href', response.url);
                        viewedObj.removeClass('hide');
                    }
                });
            }
        }
    });
}

function deleteFile() {
    Swal.fire({
          title: "Are you sure?",
          text: "You won't be able to revert this!",
          icon: "warning",
          showCancelButton: true,
          confirmButtonColor: "#3085d6",
          cancelButtonColor: "#d33",
          confirmButtonText: "Yes, delete it!"
        }).then((result) => {
      if (result.isConfirmed) {
        $.ajaxSetup({
          headers: {
            "X-CSRFToken": getDjangoCookie(),
            "X-File-ID": getHiddenInputChecksum(),
          }
        });
        $.ajax({
          url: uploadURL,
          type: 'DELETE',
          dataType: 'json',
          cache: false,
          processData: false,
          contentType: false,
          error: function (response) {
            let errorMessage = response.statusText;
            if (response.responseJSON) {
              errorMessage = response.responseJSON.message;
            }
            Swal.fire({
              title: "Error!",
              text: errorMessage,
              icon: "error"
            });
          },
          success: function () {
            let timerInterval;
            Swal.fire({
              title: "Deleted!",
              icon: "success",
              html: "I will redirect in <b></b> milliseconds.",
              showCloseButton: true,
              timer: 2000,
              timerProgressBar: true,
              didOpen: () => {
                Swal.showLoading();
                const timer = Swal.getPopup().querySelector("b");
                timerInterval = setInterval(() => {
                  timer.textContent = `${Swal.getTimerLeft()}`;
                }, 100);
              },
              willClose: () => {
                clearInterval(timerInterval);
              }
            }).then((result) => {
              if (result.dismiss === Swal.DismissReason.timer) {
                window.location.href = document.referrer;
              } else {
                window.location.href = document.referrer;
              }
            });
          }
        });

      }
    });
}

function startUpload(evt) {
    preventDefaults(evt);
    if (evt.originalEvent.submitter.name === '_delete') {
        deleteFile();
    } else {
        if ($(evt.target).find(getHiddenInput()).length && uploadFiles.length > 0) {
            let submitButton = $('button[type=submit]');
            submitButton.addClass('disabled');
            uploadFiles.forEach((file, i) => {
                console.log(`start upload file[${i}].name = ${file.name}`);
                updateStatus(file.checksum, 'Starting to upload...', 'warning');
                uploadFile(evt, file);
            });
            submitButton.removeClass('disabled');
        }
    }
}

function preventDefaults(evt) {
    evt.preventDefault();
    evt.stopPropagation();
}

function getHiddenInput() {
    return $('input[data-id=dropzone]');
}

function getHiddenInputChecksum() {
    return getHiddenInput().attr('data-value')
}

function isMultipleFile() {
    return !!getHiddenInput().attr('multiple');
}

function isImageFile(file) {
    return ['image/jpeg', 'image/png', 'image/webp', 'image/gif'].includes(file.type);
}


function openFile(evt) {
    preventDefaults(evt)
    getHiddenInput().click();
}

function clearFile() {
    [...$('.preview-file')].forEach((node) => {
        node.remove();
    });
    uploadFiles = [];
}

function addFile(file) {
    updateLoader(true);
    getCheckSum(file, function (md5) {
        updateLoader(false);
        file.checksum = md5;
        if (findFile(file)) {
            toastr.error(`File: ${file.name} is already exists.`);
            return
        }
        previewFile(file);
        uploadFiles.push(file);
        $('.btn-actions').removeClass('hide');
    });
}

function findFile(file) {
    return uploadFiles.find(function (existingFile) {
        return (existingFile.checksum === file.checksum)
    })
}

function hideBtnAction() {
    if (Array.isArray(uploadFiles) && uploadFiles.length === 0) {
        $('.btn-actions').addClass('hide');
    }
}

function removeFile(evt) {
    let currFile = $(evt).closest('.file-item');
    uploadFiles.forEach((file, index) => {
        if (file.checksum === currFile.id) {
            uploadFiles.splice(index, 1);
            return true;
        }
    });
    $(evt).closest('.preview-file').remove();
    hideBtnAction();
}

function previewFile(file) {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onloadend = function (e) {
        let imageSrc = placeholderIcon;
        if (isImageFile(file)) {
            imageSrc = e.target.result;
        }
        const previewHTML = `
            <div class="preview-file">
                <img src="${imageSrc}" class="preview-image" alt="${file.name}">
                <div class="file-item" id="${file.checksum}">
                    <div class="file-info">
                        <div class="info">
                            <span class="size">${formatBytes(file.size)}</span> -
                            <span class="title">${file.name}</span>
                        </div>
                        <div class="actions">
                            <div class="viewed">
                                <a class="text-primary hide" href="#viewed" target="_blank">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-eye-fill" viewBox="0 0 16 16">
                                        <path d="M10.5 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0"/>
                                        <path d="M0 8s3-5.5 8-5.5S16 8 16 8s-3 5.5-8 5.5S0 8 0 8m8 3.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7"/>
                                    </svg>
                                </a>
                            </div>
                            <div class="removed">
                                <a class="text-danger" href="#removed" onclick="removeFile(this)">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-x-lg" viewBox="0 0 16 16">
                                        <path d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8z"/>
                                    </svg>
                                </a>
                            </div>
                        </div>
                    </div>
                    <div class="progress">
                        <div class="progress-bar" role="progressbar" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                    <div class="progress-status">
                        <div class="status text-secondary">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-exclamation-square-fill" viewBox="0 0 16 16">
                                <path d="M2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2zm6 4c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995A.905.905 0 0 1 8 4m.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/>
                            </svg>
                            <strong>Ready to upload.</strong>
                        </div>
                    </div>
                </div>
            </div>
        `;
        $('#dropzone-preview').append(previewHTML);
    };
}

function formatBytes(bytes, decimals = 2) {
    if (!+bytes) return '0 Bytes'

    const k = 1024
    const dm = decimals < 0 ? 0 : decimals
    const sizes = ['Bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']

    const i = Math.floor(Math.log(bytes) / Math.log(k))

    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}

function updateError(currentForm, errors) {
    let errorDiv = $("<div>").attr({"class": "errornote"}).append("<h3 class='title'>Please correct the errors below:</h3>");
    let errorList = $("<ul>").attr({
        "id": "errors",
        "class": "errors"
    });
    errors.forEach((error) => {
        errorList.append($('<li>').text(error));
    });
    $(errorDiv).append(errorList);
    $(currentForm).prepend(errorDiv);
}

function updateStatus(checksum, msg, mode = 'danger') {
    [...$('.file-item')].forEach((node) => {
        if (node.id === checksum) {
            const status = $(node).find('.progress-status');
            status.empty();
            status.append(
                `
                <div class="status text-${mode}">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-exclamation-square-fill" viewBox="0 0 16 16">
                        <path d="M2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2zm6 4c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995A.905.905 0 0 1 8 4m.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/>
                    </svg>
                    <strong>${msg}</strong>
                </div>
                `
            )
        }
    });
}

function updateProgressBar(checksum, percent, backgroundColor = '#0d6efd') {
    let progressBar = $(`#${checksum} .progress-bar`);
    progressBar.attr('style', `width: ${percent}%; background-color: ${backgroundColor} !important;`);
    progressBar.text(`${percent}%`);
}


function updateLoader(open = true) {
    const loader = $('.dropzone-wrapper .loader');
    const dropzone = $('.dropzone-wrapper .dropzone');
    if (loader) {
        if (open) {
            loader.removeClass('hide');
            dropzone.addClass('blur');
        } else {
            loader.addClass('hide');
            dropzone.removeClass('blur');
        }
    }
}

function getCheckSum(file, callback) {
    let blobSlice = File.prototype.slice || File.prototype.mozSlice || File.prototype.webkitSlice,
        chunks = Math.ceil(file.size / uploadChunkSize),
        currentChunk = 0,
        spark = new SparkMD5.ArrayBuffer(),
        fileReader = new FileReader();

    fileReader.onload = function (e) {
        console.log('read chunk', currentChunk + 1, 'of', chunks);
        spark.append(e.target.result);
        currentChunk++;
        if (currentChunk < chunks) {
            loadNext();
        } else {
            const md5hash = spark.end();
            callback(md5hash);
        }
    };

    fileReader.onerror = function () {
        console.warn('oops, something went wrong.');
    };

    function loadNext() {
        let start = currentChunk * uploadChunkSize,
            end = ((start + uploadChunkSize) >= file.size) ? file.size : start + uploadChunkSize;

        fileReader.readAsArrayBuffer(blobSlice.call(file, start, end));
    }

    loadNext();
}

function getDjangoCookie() {
    const name = 'csrftoken';
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                return decodeURIComponent(cookie.substring(name.length + 1));
            }
        }
    }
}

$(document).ready(function () {
    toastr.options.closeButton = true;
    new ChunkUploaded(window.location.href).init();
    const dragDrop = $('#dropzone-dragdrop');
    const fileInput = $('input[data-id=dropzone]');
    $(".removed").on("click", function () {
        console.log("Handler for `click` called.");
    });

    dragDrop.on("click", function (evt) {
        openFile(evt);
    });

    dragDrop.on("dragover", function (evt) {
        preventDefaults(evt);
        $(evt.target).addClass(evt.target, 'drag-over');
    });

    dragDrop.on("dragenter", function (evt) {
        preventDefaults(evt);
        $(evt.target).addClass('drag-enter');
    });

    dragDrop.on("dragleave", function (evt) {
        preventDefaults(evt);
        $(evt.target).removeClass('drag-over');
    });

    dragDrop.on("drop", function (evt) {
        preventDefaults(evt);
        $(evt.target).removeClass('drag-enter');
        $(evt.target).removeClass('drag-over');
        if (isMultipleFile()) {
            if (evt.originalEvent.dataTransfer.items) {
                [...evt.originalEvent.dataTransfer.items].forEach((item, i) => {
                    if (item.kind === "file") {
                        const file = item.getAsFile();
                        console.log(`add file[${i}].name = ${file.name}`);
                        addFile(file);
                    }
                });
            } else {
                [...evt.originalEvent.dataTransfer.files].forEach((file, i) => {
                    console.log(`add file[${i}].name = ${file.name}`);
                    addFile(file);
                });
            }
        } else {
            if (evt.originalEvent.dataTransfer.files.length > 1) {
                toastr.warning('The form is a single input file, the first file to be processed. You should drop it into a single file.');
            }
            clearFile();
            const file = evt.originalEvent.dataTransfer.files[0];
            console.log(`add file.name = ${file.name}`);
            addFile(file);
        }
    });

    fileInput.on("change", function (evt) {
        if (isMultipleFile()) {
            [...evt.target.files].forEach((file, i) => {
                console.log(`add file[${i}].name = ${file.name}`);
                addFile(file);

            });
        } else {
            const file = evt.target.files[0];
            console.log(`add file.name = ${file.name}`);
            clearFile();
            addFile(file);
        }
        evt.target.value = '';
    });

    $(".btn-add-file").on("click", function (evt) {
        openFile(evt);
    });

    $("form").submit(function (evt) {
        startUpload(evt);
    });

    $(".btn-cancel").on("click", function () {
        clearFile();
        hideBtnAction();
    });
});
