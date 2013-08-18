#!/usr/bin/env python
# -*- coding: utf-8 -*-

from upload_tagged_photos import ImageUploader

def TestUploadWiki():

    url = "http://clevelandwiki.org/api/"
    user_name = raw_input("What is your username?")
    api_key = getpassword("What is your api_key?")

    def setup(self):

        self.api = slumber.API(self.url, auth=(self.user_name,
                                               self.password))

        # create two directories with some images, some should have correct
        # tags

        # create test page
        page_dict = {
                "content": "<p>The Upload Test Page.</p>",
                "name": "Upload Test Page",
        }
        test_page = self.api.page.post(page_dict)
        test_page_slug = self.api.page(test_page['id'])['slug']

        # add an image to it
        with open('image.jpg') as f:
            self.api.file.post(name='image.jpg', slug=test_page_slug,
                            files={'file': f})

        self.uploader = ImageUploader(self.api_url,
                                      user_name=self.user_name,
                                      api_key=self.api_key)

    def test_init(self):

        uploader = ImageUploader(self.api_url, user_name=self.user_name,
                                 api_key=self.api_key)

        assert self.api._store['base_url'] == self.api_url
        assert self.api._store['format'] == 'json'
        assert sefl.api._store['session'].auth[0] == self.user_name
        assert sefl.api._store['session'].auth[1] == self.api_key

    def test_remove_tmp_dirs():
        directories = ['localwikidir1', 'localwikidir1']
        for directory in directories:
            os.mkdir(os.path.join('/tmp', directory,
                                  self.uploader._tmp_dir_name))
        files = ['file1.jpg', 'file2.jpg']
        file_paths = []
        for directory, file_name in zip(directores, files):
            file_path = os.path.join('/tmp', directory,
                                     self.uploader._tmp_dir_name, file_name)
            with open(file_path, 'w') as f:
                pass
            file_path.append()
            assert os.exists(file_path)

        self.uploader.remove_tmp_dirs(file_paths)

        for file_path in file_paths:
            assert not os.exists(os.split(file_path)[0])
            assert not os.exists(file_path)

        for directory in directories:
            shutil.rmtree(os.path.join('/tmp', directory))

    def test_find_files_in_page(self):

        assert find_files_in_page('this will never be the name of a page') is None
        files_in_page = find_files_in_page('Upload Test Page')
        assert files_in_page[0]['name'] = 'image.jpg'
        assert files_in_page[0]['slug'] = 'upload test page'

    def teardown():
        # remove the files attached to the test page
        # delete the test page and all versions
        # delete the tmp image directories
        test_page = api.page('Upload Test Page').get()
        test_file_id = \
            api.files.get(slug=test_page['slug'])['objects'][0]['id']
        self.api.files.id.delete()
        self.api.page('Upload Test Page').delete()



def test_find_wiki_images():
    os.mkdir('/tmp/wiki-images')

upload_wiki_images('dir'])
upload_wiki_images(['dir1', 'dir2'])
upload_wiki_images('dir'], create_new_page=True, embed_image_on_create=True)

wiki_images = find_wiki_images('dir')
wiki_images = find_wiki_images(['dir1', 'dir2'])

wiki_images['/tmp/cw/test_image.jpg'] == ['page:Test Page']

check_if_file_exists(file_name)


